"""
This code is based on https://github.com/WongKinYiu/yolov7
"""

import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch
import yaml
from torchvision import transforms
from torchvision.ops import roi_align

from .models.utils.letterbox import letterbox
from .models.utils.general import non_max_suppression_mask_conf

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """
    Detection of an object in an image.
    """

    mask: np.ndarray
    """Binary mask of the detected object in the image."""
    class_name: str
    """Name of the class of the detected object."""
    confidence: float
    """Confidence of the detection."""


class YOLOv7:
    def __init__(self, weights_file_path: Path, hyperparameters_file_path: Path):
        """
        Initializes a YOLOv7 detector.

        Args:
            weights_file_path: Path to the file containing the weights for the model.
            hyperparameters_file_path: Path to a YAML file containing the hyperparameters for the model.
        """
        logger.info("Loading the model...")
        start_time = time.perf_counter()

        # load the hyperparameters
        with hyperparameters_file_path.open() as f:
            self.hyp = yaml.load(f, Loader=yaml.FullLoader)

        # append the models directory to the system path for torch.load to work
        models_directory = Path(__file__).parent
        sys.path.append(str(models_directory))

        # load the model
        self.device = torch.device("cpu")
        weights = torch.load(str(weights_file_path), weights_only=False)
        self.model = weights["model"]
        self.model = self.model.float().to(self.device)
        _ = self.model.eval()

        logger.info(
            f"Loaded the model in {(time.perf_counter() - start_time) * 1000:.0f} ms."
        )

    def detect(self, image: np.ndarray) -> list[Detection]:
        """
        Runs inference on the given image.

        Args:
            image: Image to detect people in.

        Returns:
            OpenCV contours of the detected people.
        """

        logger.debug("Running inference...")
        start_time = time.perf_counter()

        # get original image size
        original_height, original_width = image.shape[:2]

        # prepare image tensor
        image_letterboxed, _, (letterbox_w_padding, letterbox_h_padding) = letterbox(
            image, 640, stride=64, auto=True
        )
        image_tensor = transforms.ToTensor()(image_letterboxed)
        image_tensor = torch.tensor(np.array([image_tensor.numpy()]))
        image_tensor = image_tensor.to(self.device)
        image_tensor = image_tensor.float()

        # run inference
        output = self.model(image_tensor)
        inf_out, train_out, attn, mask_iou, bases, sem_output = (
            output["test"],
            output["bbox_and_cls"],
            output["attn"],
            output["mask_iou"],
            output["bases"],
            output["sem"],
        )

        # ...

        bases = torch.cat([bases, sem_output], dim=1)
        nb, _, tensor_height, tensor_width = image_tensor.shape
        names = self.model.names
        pooler_scale = self.model.pooler_scale

        def pooler(features: torch.Tensor, boxes: list):
            """
            A replacement for Detectron2's ROIPooler using torchvision's roi_align.
            """
            return roi_align(
                features,
                boxes,
                output_size=self.hyp["mask_resolution"],
                spatial_scale=pooler_scale,
                sampling_ratio=-1,
            )

        # NMS

        output, output_mask, output_mask_score, output_ac, output_ab = (
            non_max_suppression_mask_conf(
                inf_out,
                attn,
                bases,
                pooler,
                self.hyp,
                conf_thres=0.25,
                iou_thres=0.65,
                merge=False,
                mask_iou=None,
            )
        )

        pred, pred_masks = output[0], output_mask[0]

        # if nothing is detected, return an empty list
        if (pred is None) or (pred_masks is None):
            logger.debug(
                f"Ran inference in {(time.perf_counter() - start_time) * 1000:.0f} ms, no detections."
            )
            return []

        # boxes (rescaled to negate letterboxing effect)
        bboxes = pred[:, :4]
        bboxes[:, 0] = bboxes[:, 0] - letterbox_w_padding
        bboxes[:, 2] = bboxes[:, 2] - letterbox_w_padding
        bboxes[:, 1] = bboxes[:, 1] - letterbox_h_padding
        bboxes[:, 3] = bboxes[:, 3] - letterbox_h_padding

        # classes and confidences
        pred_cls = pred[:, 5].detach().cpu().numpy()
        pred_conf = pred[:, 4].detach().cpu().numpy()

        # masks
        original_pred_masks = pred_masks.view(
            -1, self.hyp["mask_resolution"], self.hyp["mask_resolution"]
        )
        pred_masks = self._paste_masks_in_image(
            original_pred_masks,
            bboxes,
            (
                int(tensor_height - letterbox_h_padding * 2),
                int(tensor_width - letterbox_w_padding * 2),
            ),
            threshold=0.5,
        )
        pred_masks_np = pred_masks.detach().cpu().numpy()

        logger.debug(
            f"Ran inference and post-processing in {(time.perf_counter() - start_time) * 1000:.0f} ms."
        )

        detections = [
            Detection(
                mask=self._resize_mask(mask_np, original_height, original_width),
                class_name=names[int(cls)] if (0 <= cls < len(names)) else "unknown",
                confidence=conf,
            )
            for (mask_np, cls, conf) in zip(pred_masks_np, pred_cls, pred_conf)
        ]

        return detections

    @staticmethod
    def _resize_mask(mask: np.ndarray, height: int, width: int) -> np.ndarray[bool]:
        """
        Resize the boolean mask to the original image resolution.

        Args:
            mask: The mask to upscale. Should be of dtype bool.
            height: The height of the original image.
            width: The width of the original image.

        Returns:
            The resized boolean mask.
        """
        return cv2.resize(
            mask.astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST
        ).astype(bool)

    @staticmethod
    def _paste_masks_in_image(
        masks: torch.Tensor,
        boxes: torch.Tensor,
        img_shape: tuple,
        threshold: float = 0.5,
    ):
        """
        Paste segmented masks onto an image.

        Args:
            masks: a tensor of shape (N, H_mask, W_mask), N masks of size H_mask x W_mask.
            boxes: a tensor of shape (N, 4), boxes in (x1, y1, x2, y2) format.
            img_shape: shape of the target image, in (height, width).
            threshold: a float in [0, 1]. Areas with a mask value > threshold will be pasted.

        Returns:
            torch.Tensor: a bool tensor of shape (N, img_shape[0], img_shape[1]).
        """

        N = masks.shape[0]
        img_h, img_w = img_shape
        output = torch.zeros(N, img_h, img_w, dtype=torch.bool)

        boxes = boxes.cpu().numpy().astype(np.int32)

        for i in range(N):
            box = boxes[i]
            x_1, y_1, x_2, y_2 = box.tolist()
            mask = masks[i]
            mask_resized = torch.nn.functional.interpolate(
                mask[None, None], size=(y_2 - y_1, x_2 - x_1), mode="bilinear"
            )[0][0]
            mask_resized = mask_resized > threshold
            output[i, y_1:y_2, x_1:x_2] = mask_resized

        return output
