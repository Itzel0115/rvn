import json
from evaluation.cli import main
from evaluation.comparison import compare_runs
from evaluation.models import EvalCaseResult
from evaluation.runner import EvaluationRunner


def test_coverage_report_gate_and_invalid_run_cli(tmp_path,monkeypatch,capsys):
    root=tmp_path/"output"/"evaluations"/"runs";aggregate=EvaluationRunner(root).run("core");run_id=aggregate["eval_run_id"]
    monkeypatch.chdir(tmp_path)
    assert main(["coverage","--run-id",run_id])==0
    payload=json.loads(capsys.readouterr().out);assert payload["actual_coverage"]["overall"]["actual_execution_completed"]==8
    assert main(["report",run_id])==0;capsys.readouterr()
    assert main(["gate",run_id])==1;capsys.readouterr()
    assert main(["coverage","--run-id","does-not-exist"])==2


def _write_run(folder,run_id,rows,score):
    folder.mkdir();(folder/"aggregate.json").write_text(json.dumps({"schema_version":"scorecard.v1","eval_run_id":run_id,"overall_score":score,"hard_invariant_pass_rate":1.0}),encoding="utf-8")
    with (folder/"case_results.jsonl").open("w",encoding="utf-8") as handle:
        for row in rows: handle.write(json.dumps(row.to_dict())+"\n")


def _row(case_id,passed,score):
    return EvalCaseResult(case_id,"trace-"+case_id,"completed",[],passed,score,[],execution_mode="execution_backed",suite="core",execution_adapter="assistant",actual_execution_mode="execution_backed",adapter_status="completed",actual_execution_attempted=True,actual_execution_completed=True,actual_execution_passed=passed)


def test_comparison_emits_case_level_improved_unchanged_regressed_new_and_fixed(tmp_path):
    base=tmp_path/"base";candidate=tmp_path/"candidate"
    _write_run(base,"base",[_row("a",True,.5),_row("b",True,.5),_row("c",True,.8),_row("d",False,.2),_row("e",True,.8)],.56)
    _write_run(candidate,"candidate",[_row("a",True,.7),_row("b",True,.5),_row("c",True,.6),_row("d",True,.8),_row("e",False,.2)],.56)
    result=compare_runs(base,candidate)
    assert result["case_level"]["improved"]==["a"]
    assert result["case_level"]["unchanged"]==["b"]
    assert result["case_level"]["regressed"]==["c"]
    assert result["case_level"]["fixed_failure"]==["d"]
    assert result["case_level"]["new_failure"]==["e"]
    for name in ("comparison.json","comparison.md","case_deltas.csv"): assert (candidate/name).exists()


def test_comparison_rejects_incompatible_schema(tmp_path):
    base=tmp_path/"base";candidate=tmp_path/"candidate";_write_run(base,"base",[_row("a",True,1)],1);_write_run(candidate,"candidate",[_row("a",True,1)],1)
    payload=json.loads((candidate/"aggregate.json").read_text());payload["schema_version"]="different.v1";(candidate/"aggregate.json").write_text(json.dumps(payload))
    import pytest
    with pytest.raises(ValueError,match="incompatible_scorecard_schema"): compare_runs(base,candidate)
