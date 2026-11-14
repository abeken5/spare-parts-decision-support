import numpy as np
from src.segmentation.classify import (
    compute_adi_cv2,
    classify_syntetos_boylan,
    classify_xyz,
)


def test_syntetos_boylan_quadrants_and_boundaries():
    assert classify_syntetos_boylan(1.31, 0.48) == "Smooth"
    assert classify_syntetos_boylan(1.31, 0.49) == "Erratic"
    assert classify_syntetos_boylan(1.32, 0.48) == "Intermittent"
    assert classify_syntetos_boylan(1.32, 0.49) == "Lumpy"


def test_compute_adi_cv2_edge_cases():
    # All-zero demand
    adi_zero, cv2_zero = compute_adi_cv2(np.zeros(24))
    assert np.isinf(adi_zero)
    assert cv2_zero == 0.0

    # Single non-zero demand in 24 periods -> ADI = 24.0, CV2 = 0.0
    single = np.zeros(24)
    single[5] = 10
    adi_s, cv2_s = compute_adi_cv2(single)
    assert adi_s == 24.0
    assert cv2_s == 0.0

    # Constant positive demand every period -> ADI = 1.0, CV2 = 0.0
    const = np.full(12, 5.0)
    adi_c, cv2_c = compute_adi_cv2(const)
    assert adi_c == 1.0
    assert cv2_c == 0.0


def test_xyz_classification():
    _, cls_x = classify_xyz(np.array([10, 10, 11, 9, 10, 10]))
    _, cls_y = classify_xyz(np.array([2, 10, 4, 12, 3, 11]))
    _, cls_z = classify_xyz(np.array([0, 0, 0, 25, 0, 0]))
    _, cls_zero = classify_xyz(np.zeros(12))

    assert cls_x == "X"
    assert cls_y == "Y"
    assert cls_z == "Z"
    assert cls_zero == "Z"
