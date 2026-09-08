from src import config

def test_six_supply_files_plus_map():
    """
    Test src.config has 6 supply files and a map file.
    """
    assert len(config.SUPPLY_FILES) == 6
    assert config.MAP_FILE == "pbs-item-drug-map.csv"

def test_stage_months_are_policy_dates():
    """
    Test src.config has stage months that are policy dates.
    """
    assert config.STAGE_MONTHS == {1: 202309, 2: 202403, 3: 202409}

def test_multiplier_is_two():
    """
    Test src.config has multiplier of 2.
    """
    assert config.SUPPLY_MULTIPLIER == 2