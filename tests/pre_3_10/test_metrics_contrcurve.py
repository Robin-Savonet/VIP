"""
Tests for metrics/contrcurve.py

"""
import copy
import sys

from tests.helpers import fixture
from tests.helpers import np
from vip_hci.config import VLT_NACO
from vip_hci.fm import cube_planet_free
from vip_hci.fm.utils_negfc import find_nearest
from vip_hci.metrics import contrast_curve
from vip_hci.preproc import frame_crop
from vip_hci.psfsub import pca
from vip_hci.psfsub import PCA_Params

sys.path.append(".../tests")

sys.path.append(".../tests")


@fixture(scope="module")
def get_cube(example_dataset_adi):
    """
    Get the ADI sequence from conftest.py.

    Parameters
    ----------
    example_dataset_adi : fixture
        Taken automatically from ``conftest.py``.

    Returns
    -------
    dsi : VIP Dataset

    """
    dsi = copy.copy(example_dataset_adi)

    starphot = 764939.6  # Absil et al. (2013)

    return dsi, starphot


def test_contrast_curve(get_cube):
    ds, starphot = get_cube

    # first empty the cube from planet b
    r_b = 0.452 / ds.px_scale  # Absil+2013
    theta_b = 211.0 + 90  # + 104.84 - 0.45 (incl. in derot_angs now) Absil+2013
    flux_b = 550.2
    pl_par = [(r_b, theta_b, flux_b)]
    cube = cube_planet_free(pl_par, ds.cube, ds.angles, ds.psf)

    psf = frame_crop(ds.psf[1:, 1:], 11)
    plsc = VLT_NACO["plsc"]
    trans = np.zeros([2, 10])
    trans[0] = np.linspace(0, cube.shape[-1], 10)
    trans[1, :] = np.linspace(0.999, 1, 10, endpoint=False)
    cc = contrast_curve(
        cube,
        ds.angles,
        psf,
        ds.fwhm,
        pxscale=plsc,
        starphot=starphot,
        algo=pca,
        nbranch=3,
        ncomp=4,
        transmission=trans,
        plot=True,
        debug=True,
        algo_class=PCA_Params,
    )

    rad = np.array(cc["distance"])
    gauss_cc = np.array(cc["sensitivity_gaussian"])
    student_cc = np.array(cc["sensitivity_student"])
    sigma_corr = np.array(cc["sigma corr"])

    # check that at 0.2'' 5-sigma cc < 4e-3 - Gaussian statistics
    thr02 = 6e-3
    idx_r = find_nearest(rad * plsc, 0.2)
    cc_gau = gauss_cc[idx_r]
    corr_r = sigma_corr[idx_r]
    if cc_gau < thr02:
        check = True
    else:
        check = False
    msg = "Contrast too shallow compared to expectations: {} > {}"
    assert check, msg.format(cc_gau, thr02)

    # check that at 0.2'' 5-sigma cc: Student statistics > Gaussian statistics
    cc_stu = student_cc[idx_r]
    if cc_stu < thr02 * corr_r and cc_stu > cc_gau:
        check = True
    elif cc_stu < thr02 * corr_r:
        check = False
        msg = "Student-statistics cc smaller than Gaussian statistics cc"
    else:
        check = False
    msg = "Contrast too shallow compared to expectations: {} > {}"
    assert check, msg.format(cc_stu, thr02 * corr_r)

    # check that at 0.4'' 5-sigma cc < 5e-4
    thr04 = 8e-4
    idx_r = find_nearest(rad * plsc, 0.4)
    cc_gau = gauss_cc[idx_r]
    corr_r = sigma_corr[idx_r]

    if cc_gau < thr04:
        check = True
    else:
        check = False
    msg = "Contrast too shallow compared to expectations: {} > {}"
    assert check, msg.format(cc_gau, thr04)

    # check that at 0.4'' 5-sigma cc: Student statistics > Gaussian statistics
    cc_stu = student_cc[idx_r]
    if cc_stu < thr04 * corr_r and cc_stu > cc_gau:
        check = True
    elif cc_stu < thr04 * corr_r:
        check = False
        msg = "Student-statistics cc smaller than Gaussian statistics cc"
    else:
        check = False
        msg = "Contrast too shallow compared to expectations: {} > {}"
    assert check, msg.format(cc_stu, thr04 * corr_r)
