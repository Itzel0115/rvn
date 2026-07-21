from evaluation.datasets import list_suites,load_suite,validate_cases

def test_versioned_datasets_have_more_than_required_cases_and_validate():
    cases=[case for suite in list_suites() for case in load_suite(suite)]
    assert len(cases)>=36 and not validate_cases(cases) and len({c.case_id for c in cases})==len(cases)
