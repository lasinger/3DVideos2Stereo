#!/usr/bin/env python
""" 
    Generate disparity and uncertainty maps for given list. 
    Assumumption: (full-resolution; i.e. 1880x800) forward / backward flow is located 
    in the folders flow_forward and flow_backward.
"""
import os
import argparse
import numpy as np
import cv2
from PIL import PngImagePlugin
import imageio


def read_flow(filename):
    # TODO: Replace with your code to read a flow field
    u = np.zeros((1880, 800))
    v = np.zeros((1880, 800))

    return u, v


def get_disp_and_uncertainty(
    filenames,
    use_filtering,
    v_threshold,
    max_v_fail,
    fbc_threshold,
    min_fbc_pass,
    range_threshold,
):
    for i, filename in enumerate(filenames):
        print(f"{i + 1} / {len(filenames)}: {filename}")

        # read flow
        u_fw, v_fw = read_flow("flow_forward/" + filename + ".flo")
        u_bw, v_bw = read_flow("flow_backward/" + filename + ".flo")

        if use_filtering:
            check_v_fw = abs(v_fw) > v_threshold
            v_fail_fw = 1.0 * np.count_nonzero(check_v_fw) / v_fw.size

            if v_fail_fw >= max_v_fail:
                print("v_fail_fw too large")
                continue

            check_v_bw = abs(v_bw) > v_threshold
            v_fail_bw = 1.0 * np.count_nonzero(check_v_bw) / v_bw.size

            if v_fail_bw >= max_v_fail:
                print("v_fail_bw too large")
                continue

            range_fw = u_fw.max() - u_fw.min()

            if range_fw <= range_threshold:
                print("range_u_fw too small")
                continue

            range_bw = u_bw.max() - u_bw.min()

            if range_bw <= range_threshold:
                print("range_u_bw too small")
                continue

        # compute uncertainty and disparity
        ind_y, ind_x = np.indices(u_fw.shape, dtype=np.float32)
        y_map = ind_y
        x_map = ind_x + u_fw

        flow_flipped_and_warped = cv2.remap(
            -u_bw,
            x_map,
            y_map,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )

        uncertainty = abs(u_fw - flow_flipped_and_warped)

        if use_filtering:
            valid = uncertainty < fbc_threshold
            fbc_pass = 1.0 * np.count_nonzero(valid) / uncertainty.size

            if fbc_pass <= min_fbc_pass:
                print("fbc_pass too small")
                continue

        disp = -u_fw

        # downsample disparity and uncertainty
        downscaling = 0.5

        disp = cv2.resize(
            disp, None, fx=downscaling, fy=downscaling, interpolation=cv2.INTER_LINEAR
        )

        disp = disp * downscaling

        uncertainty = cv2.resize(
            uncertainty,
            None,
            fx=downscaling,
            fy=downscaling,
            interpolation=cv2.INTER_LINEAR,
        )

        uncertainty = uncertainty * downscaling

        # quantize disparity and uncertainty
        disp_max = disp.max()
        disp_min = disp.min()

        if disp_max - disp_min > 0:
            disp = np.round((disp - disp_min) / (disp_max - disp_min) * 65535).astype(
                np.uint16
            )

            scale = 1.0 * (disp_max - disp_min) / 65535
            offset = disp_min
        else:
            disp = (0 * disp).astype(np.uint16)

            offset = disp_min
            scale = 1.0

        meta = PngImagePlugin.PngInfo()
        meta.add_text("offset", str(offset))
        meta.add_text("scale", str(scale))

        uncertainty = (10 * uncertainty).round()
        uncertainty[uncertainty > 255] = 255

        # save disparity and uncertainty
        disp_name = "disparity/" + filename + ".png"

        if not os.path.exists(os.path.dirname(disp_name)):
            os.makedirs(os.path.dirname(disp_name))

        imageio.imwrite(disp_name, disp, pnginfo=meta, prefer_uint8=False)

        uncertainty_name = "uncertainty/" + filename + ".png"

        if not os.path.exists(os.path.dirname(uncertainty_name)):
            os.makedirs(os.path.dirname(uncertainty_name))

        imageio.imwrite(uncertainty_name, uncertainty.astype(np.uint8))


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        description="Generate disparity and uncertainty maps for given list. Assumumption: (full-resolution; i.e. 1880x800) forward / backward flow is located in the folders flow_forward and flow_backward."
    )
    PARSER.add_argument("list", type=str, help="path to list file")
    PARSER.add_argument(
        "-f", "--filter", action="store_true", help="Apply filtering based on flow?"
    )
    PARSER.add_argument(
        "--v_threshold", type=float, default=2, help="threshold vertical flow check"
    )
    PARSER.add_argument(
        "--max_v_fail",
        type=float,
        default=0.1,
        help="max percentage of pixels that fail vertical flow check",
    )
    PARSER.add_argument(
        "--fbc_threshold",
        type=float,
        default=2,
        help="threshold for forward-backward check",
    )
    PARSER.add_argument(
        "--min_fbc_pass",
        type=float,
        default=0.7,
        help="min percentage of pixels that pass forward-backward check",
    )
    PARSER.add_argument(
        "--range_threshold",
        type=float,
        default=10,
        help="threshold for horizontal flow range check",
    )
    ARGS = PARSER.parse_args()

    with open(ARGS.list, "r") as f:
        FILENAMES = [line.rstrip("\n") for line in f]

    get_disp_and_uncertainty(
        FILENAMES,
        ARGS.filter,
        ARGS.v_threshold,
        ARGS.max_v_fail,
        ARGS.fbc_threshold,
        ARGS.min_fbc_pass,
        ARGS.range_threshold,
    )
