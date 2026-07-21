from evaluation.models import EvalCase,EvalCaseResult,GraderResult

def test_eval_models_are_json_safe_dataclasses():
    case=EvalCase("c","core","x","x","question","x")
    result=EvalCaseResult(case.case_id,"t","completed",[GraderResult("g","v",1,True,"info","ok")],True,1,[])
    assert result.to_dict()["case_id"]=="c" and case.to_dict()["schema_version"]=="evaluation.v1"
