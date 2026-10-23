import asyncio
import logging
import math
import time
from collections.abc import AsyncGenerator, Mapping, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, CatBoostError, Pool

from app.schemas.prediction import CreditScoringFeatures, PredictionResult
from app.shared.config import DEFAULT_MODEL_PATH, settings
from app.shared.exceptions import (
    ModelInferenceError,
    ModelLoadError,
    ModelNotLoadedError,
)

logger = logging.getLogger(__name__)

_LOG1P_FEATURES: frozenset[str] = frozenset({"loan_amount_rub", "employees_count"})

type FeatureRecord = CreditScoringFeatures | Mapping[str, Any]
type ModelInput = (
    Pool
    | pd.DataFrame
    | np.ndarray
    | FeatureRecord
    | Sequence[FeatureRecord]
    | Sequence[Sequence[Any]]
)


def _normalize_cat_value(value: Any) -> str:
    """Normalize categorical feature value to the string representation expected by CatBoost."""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


class CatBoostModelService:
    """High-performance inference service for CatBoostClassifier (model-test.cbm)."""

    __slots__ = (
        "_cat_feature_indices",
        "_cat_feature_names",
        "_feature_names",
        "_is_loaded",
        "_model",
        "_model_path",
        "_thread_count",
    )

    def __init__(
        self,
        model_path: Path | str = settings.MODEL_PATH,
        *,
        thread_count: int = settings.MODEL_THREAD_COUNT,
        auto_load: bool = True,
    ) -> None:
        self._model_path = Path(model_path)
        self._thread_count = max(1, thread_count)
        self._model = CatBoostClassifier()
        self._is_loaded = False
        self._feature_names: tuple[str, ...] = ()
        self._cat_feature_indices: tuple[int, ...] = ()
        self._cat_feature_names: frozenset[str] = frozenset()

        if auto_load:
            self.load(warmup=True)

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def model_path(self) -> Path:
        return self._model_path

    @property
    def feature_names(self) -> tuple[str, ...]:
        self._ensure_loaded()
        return self._feature_names

    @property
    def cat_feature_indices(self) -> tuple[int, ...]:
        self._ensure_loaded()
        return self._cat_feature_indices

    @property
    def cat_feature_names(self) -> frozenset[str]:
        self._ensure_loaded()
        return self._cat_feature_names

    def load(self, *, warmup: bool = True) -> None:
        """Load the .cbm model from disk into memory and optionally warm up C++ buffers."""
        if not self._model_path.is_file():
            raise ModelLoadError(f"Model file not found at: {self._model_path}")

        start_ts = time.perf_counter()
        try:
            model = CatBoostClassifier()
            model.load_model(str(self._model_path), format="cbm")
        except (CatBoostError, OSError) as exc:
            raise ModelLoadError(
                f"Failed to load CatBoost model from {self._model_path}: {exc}"
            ) from exc

        self._model = model
        self._feature_names = tuple(model.feature_names_)
        self._cat_feature_indices = tuple(model.get_cat_feature_indices())
        self._cat_feature_names = frozenset(
            self._feature_names[idx] for idx in self._cat_feature_indices
        )
        self._is_loaded = True

        if warmup and self._feature_names:
            self._warmup()

        elapsed_ms = (time.perf_counter() - start_ts) * 1000
        logger.info(
            f"[ML] Loaded model '{self._model_path.name}' "
            f"({len(self._feature_names)} features, {len(self._cat_feature_indices)} categorical) "
            f"in {elapsed_ms:.2f} ms"
        )

    def _warmup(self) -> None:
        """Execute a dummy single-row pass to warm up CatBoost internal structures."""
        dummy_row = [
            "0" if idx in self._cat_feature_indices else 0.0
            for idx in range(len(self._feature_names))
        ]
        pool = Pool(data=[dummy_row], cat_features=list(self._cat_feature_indices))
        self._model.predict_proba(pool, thread_count=1)

    def _ensure_loaded(self) -> None:
        if not self._is_loaded:
            raise ModelNotLoadedError(
                "CatBoost model is not loaded. Call service.load() before running inference."
            )

    def _extract_row(
        self,
        record: FeatureRecord,
        *,
        log_transformed: bool,
    ) -> list[Any]:
        """Extract a single feature row in exact model column order without DataFrame overhead."""
        mapping: Mapping[str, Any] = (
            record.to_feature_dict()
            if isinstance(record, CreditScoringFeatures)
            else record
        )
        row: list[Any] = []
        cat_names = self._cat_feature_names

        for name in self._feature_names:
            if name not in mapping:
                raise ModelInferenceError(f"Missing required feature: '{name}'")
            val = mapping[name]
            if name in cat_names:
                row.append(_normalize_cat_value(val))
            else:
                num_val = float(val)
                if not log_transformed and name in _LOG1P_FEATURES:
                    if num_val < 0:
                        raise ModelInferenceError(
                            f"Feature '{name}' must be non-negative for log1p transform, got {num_val}"
                        )
                    num_val = math.log1p(num_val)
                row.append(num_val)
        return row

    def _build_pool(
        self,
        test_data: ModelInput,
        *,
        log_transformed: bool = True,
    ) -> Pool:
        """Convert supported input formats into an optimized CatBoost Pool."""
        self._ensure_loaded()
        cat_indices_list = list(self._cat_feature_indices)

        try:
            if isinstance(test_data, Pool):
                return test_data

            if isinstance(test_data, pd.DataFrame):
                missing = [
                    col for col in self._feature_names if col not in test_data.columns
                ]
                if missing:
                    raise ModelInferenceError(
                        f"DataFrame is missing required features: {missing}"
                    )
                df = test_data.loc[:, list(self._feature_names)].copy()
                if not log_transformed:
                    for col in _LOG1P_FEATURES:
                        if col in df.columns:
                            df[col] = np.log1p(df[col].astype(float))
                for col in self._cat_feature_names:
                    df[col] = df[col].map(_normalize_cat_value)
                return Pool(data=df, cat_features=cat_indices_list)

            if isinstance(test_data, (CreditScoringFeatures, Mapping)):
                row = self._extract_row(test_data, log_transformed=log_transformed)
                return Pool(data=[row], cat_features=cat_indices_list)

            if isinstance(test_data, np.ndarray):
                arr = (
                    test_data
                    if test_data.ndim == 2
                    else np.expand_dims(test_data, axis=0)
                )
                return Pool(data=arr, cat_features=cat_indices_list)

            if isinstance(test_data, Sequence) and not isinstance(
                test_data, (str, bytes)
            ):
                if not test_data:
                    raise ModelInferenceError("Input test_data sequence cannot be empty.")
                first = test_data[0]
                if isinstance(first, (CreditScoringFeatures, Mapping)):
                    rows = [
                        self._extract_row(item, log_transformed=log_transformed)  # type: ignore[arg-type]
                        for item in test_data
                    ]
                    return Pool(data=rows, cat_features=cat_indices_list)
                if isinstance(first, Sequence) and not isinstance(first, (str, bytes)):
                    return Pool(data=list(test_data), cat_features=cat_indices_list)
                return Pool(data=[list(test_data)], cat_features=cat_indices_list)

            raise ModelInferenceError(
                f"Unsupported test_data type: {type(test_data).__name__}"
            )
        except ModelInferenceError:
            raise
        except (CatBoostError, ValueError, TypeError, KeyError) as exc:
            raise ModelInferenceError(f"Failed to build CatBoost Pool: {exc}") from exc

    def predict(
        self,
        test_data: ModelInput,
        *,
        log_transformed: bool = True,
        thread_count: int | None = None,
    ) -> list[int]:
        """Run class prediction (0 or 1) on test_data."""
        pool = self._build_pool(test_data, log_transformed=log_transformed)
        threads = thread_count or self._thread_count
        try:
            raw_preds = self._model.predict(pool, thread_count=threads)
            return [int(x) for x in np.asarray(raw_preds).ravel()]
        except CatBoostError as exc:
            raise ModelInferenceError(f"CatBoost prediction failed: {exc}") from exc

    def predict_proba(
        self,
        test_data: ModelInput,
        *,
        log_transformed: bool = True,
        thread_count: int | None = None,
    ) -> list[tuple[float, float]]:
        """Run probability prediction [(prob_class_0, prob_class_1), ...] on test_data."""
        pool = self._build_pool(test_data, log_transformed=log_transformed)
        threads = thread_count or self._thread_count
        try:
            probs = np.asarray(self._model.predict_proba(pool, thread_count=threads))
            return [(float(row[0]), float(row[1])) for row in probs]
        except CatBoostError as exc:
            raise ModelInferenceError(
                f"CatBoost probability prediction failed: {exc}"
            ) from exc

    def predict_one(
        self,
        features: FeatureRecord,
        *,
        log_transformed: bool = True,
    ) -> PredictionResult:
        """Predict class and probabilities for a single feature record (optimized with thread_count=1)."""
        pool = self._build_pool(features, log_transformed=log_transformed)
        try:
            probs = self._model.predict_proba(pool, thread_count=1)[0]
            default_prob = float(probs[0])
            approval_prob = float(probs[1])
            predicted_class = 1 if approval_prob >= 0.5 else 0
            return PredictionResult(
                prediction=predicted_class,
                approval_probability=approval_prob,
                default_probability=default_prob,
            )
        except CatBoostError as exc:
            raise ModelInferenceError(f"Single prediction failed: {exc}") from exc

    def predict_batch(
        self,
        test_data: ModelInput,
        *,
        log_transformed: bool = True,
        thread_count: int | None = None,
    ) -> list[PredictionResult]:
        """Predict classes and probabilities for a batch of records."""
        probs_list = self.predict_proba(
            test_data,
            log_transformed=log_transformed,
            thread_count=thread_count,
        )
        return [
            PredictionResult(
                prediction=1 if prob_1 >= 0.5 else 0,
                approval_probability=prob_1,
                default_probability=prob_0,
            )
            for prob_0, prob_1 in probs_list
        ]

    async def predict_async(
        self,
        test_data: ModelInput,
        *,
        log_transformed: bool = True,
        thread_count: int | None = None,
    ) -> list[int]:
        """Non-blocking async wrapper around predict()."""
        return await asyncio.to_thread(
            self.predict,
            test_data,
            log_transformed=log_transformed,
            thread_count=thread_count,
        )

    async def predict_one_async(
        self,
        features: FeatureRecord,
        *,
        log_transformed: bool = True,
    ) -> PredictionResult:
        """Non-blocking async wrapper around predict_one()."""
        return await asyncio.to_thread(
            self.predict_one,
            features,
            log_transformed=log_transformed,
        )

    async def predict_batch_async(
        self,
        test_data: ModelInput,
        *,
        log_transformed: bool = True,
        thread_count: int | None = None,
    ) -> list[PredictionResult]:
        """Non-blocking async wrapper around predict_batch()."""
        return await asyncio.to_thread(
            self.predict_batch,
            test_data,
            log_transformed=log_transformed,
            thread_count=thread_count,
        )


@asynccontextmanager
async def model_lifespan(
    model_path: Path | str = DEFAULT_MODEL_PATH,
    *,
    thread_count: int = 1,
) -> AsyncGenerator[dict[str, Any], None]:
    """FastAPI lifespan context manager that loads and warms up the CatBoost model once at startup."""
    service = CatBoostModelService(
        model_path=model_path,
        thread_count=thread_count,
        auto_load=False,
    )
    await asyncio.to_thread(service.load, warmup=True)
    yield {"model_service": service}
