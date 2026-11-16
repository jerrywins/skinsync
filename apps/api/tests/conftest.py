from pathlib import Path

import pytest
import yaml

from skinsync.domain.compatibility import FormulationInput
from skinsync.domain.ingredients import IngredientMaster, IngredientRecord, normalize_list
from skinsync.domain.knowledge import load_knowledge_dir

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def master() -> IngredientMaster:
    data = yaml.safe_load((FIXTURES / "ingredients.yaml").read_text())
    return IngredientMaster.from_records([IngredientRecord(**r) for r in data["ingredients"]])


@pytest.fixture(scope="session")
def fixture_kv():
    return load_knowledge_dir(FIXTURES / "knowledge", "fixture-kv-1", allow_fixture=True)


@pytest.fixture
def make_formulation(master):
    def _make(text: str, name: str = "Product", vid: str | None = None, keys=frozenset(), has_list=True):
        return FormulationInput(
            product_id=f"p-{name}",
            product_version_id=vid or f"pv-{name}",
            product_name=name,
            version_label="v1",
            ingredients=tuple(normalize_list(text, master, frozenset(keys))),
            has_ingredient_list=has_list,
        )

    return _make
