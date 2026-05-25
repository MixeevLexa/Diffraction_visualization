import numpy as np
from scipy.signal import find_peaks


class DiffractionModel:
    def __init__(self, a=100.0, F1=100.0, F2=100.0, N=5, b=20.0, d=50.0,
                 lambda_0=550.0, delta_lambda=0.0,
                 spectrum_type="mono", source_type="uniform"):
        # Store everything in SI units internally
        self.a = a * 1e-6           # source size, m
        self.F1 = F1 * 1e-3         # focal length 1, m
        self.F2 = F2 * 1e-3         # focal length 2, m
        self.N = int(N)
        self.b = b * 1e-6           # slit width, m
        self.d = d * 1e-6           # grating period, m
        self.lambda_0 = lambda_0 * 1e-9  # central wavelength, m
        self.delta_lambda = delta_lambda * 1e-9
        self.spectrum_type = spectrum_type
        self.source_type = source_type

    def compute_single(self, Y, y_s, lam):
        """Intensity for a single source point y_s and wavelength lam."""
        nu = Y / (lam * self.F2) - y_s / (lam * self.F1)

        # Single slit factor: np.sinc(x) = sin(pi*x)/(pi*x)
        single_slit = np.sinc(self.b * nu)

        # Grating factor with safe division
        phi = np.pi * self.d * nu
        denom = np.sin(phi)
        numer = np.sin(self.N * phi)

        mask = np.abs(denom) < 1e-12
        grating = np.where(
            mask,
            self.N * np.cos(self.N * phi) / np.where(np.abs(np.cos(phi)) < 1e-12, 1.0, np.cos(phi)),
            numer / np.where(mask, 1.0, denom)
        )

        return (single_slit * grating) ** 2

    def _source_points(self, n_src=150):
        if self.a < 1e-12:
            return np.array([0.0]), np.array([1.0])

        if self.source_type == "uniform":
            y_s = np.linspace(-self.a / 2, self.a / 2, n_src)
            weights = np.ones(n_src)
        else:  # gaussian
            sigma = self.a / (2 * np.sqrt(2 * np.log(2)))
            y_s = np.linspace(-2 * self.a, 2 * self.a, n_src)
            weights = np.exp(-y_s ** 2 / (2 * sigma ** 2))

        weights /= np.sum(weights)
        return y_s, weights

    def _spectrum_points(self, n_lam=80):
        if self.delta_lambda < 1e-15 or self.spectrum_type == "mono":
            return np.array([self.lambda_0]), np.array([1.0])

        sigma = self.delta_lambda / (2 * np.sqrt(2 * np.log(2)))
        lam = np.linspace(self.lambda_0 - 3 * self.delta_lambda,
                          self.lambda_0 + 3 * self.delta_lambda, n_lam)
        lam = lam[lam > 0]
        weights = np.exp(-(lam - self.lambda_0) ** 2 / (2 * sigma ** 2))
        weights /= np.sum(weights)
        return lam, weights

    def compute_total(self, Y):
        y_s_arr, w_s = self._source_points()
        lam_arr, w_l = self._spectrum_points()

        I_total = np.zeros_like(Y, dtype=np.float64)

        # Broadcasting: Y[nY,1,1], y_s[1,ns,1], lam[1,1,nl]
        # For memory efficiency, loop over wavelengths
        for j, lam in enumerate(lam_arr):
            for i, ys in enumerate(y_s_arr):
                I_total += w_s[i] * w_l[j] * self.compute_single(Y, ys, lam)

        mx = np.max(I_total)
        if mx > 0:
            I_total /= mx
        return I_total

    def compute_ideal(self, Y):
        """Intensity for point monochromatic source (reference curve)."""
        return self.compute_single(Y, 0.0, self.lambda_0) / \
               np.max(self.compute_single(Y, 0.0, self.lambda_0))

    def compute_visibility(self, Y, I):
        if len(I) < 5:
            return np.array([]), np.array([])

        # Find peaks with minimum prominence
        peak_height = np.max(I) * 0.005
        peaks, _ = find_peaks(I, height=peak_height, distance=3)

        if len(peaks) < 2:
            return np.array([]), np.array([])

        Y_vis = []
        V_vis = []

        for k in range(len(peaks) - 1):
            idx1 = peaks[k]
            idx2 = peaks[k + 1]
            if idx2 - idx1 < 2:
                continue

            I_min = np.min(I[idx1:idx2 + 1])
            I_max = 0.5 * (I[idx1] + I[idx2])

            if I_max + I_min > 1e-15:
                V = (I_max - I_min) / (I_max + I_min)
                Y_mid = 0.5 * (Y[idx1] + Y[idx2])
                Y_vis.append(Y_mid)
                V_vis.append(V)

        return np.array(Y_vis), np.array(V_vis)

    def get_Y_range(self, n_points_min=3000, n_points_max=30000):
        delta_Y_ord = self.lambda_0 * self.F2 / self.d
        n_orders = self.d / self.b
        Y_max = (n_orders + 2) * delta_Y_ord

        # Ensure enough points to resolve narrowest peak
        delta_Y_peak = self.lambda_0 * self.F2 / (self.N * self.d)
        points_needed = int(2 * Y_max / (delta_Y_peak / 12))
        n_points = max(n_points_min, min(points_needed, n_points_max))

        return np.linspace(-Y_max, Y_max, n_points)