"""Every job declares what it needs; the deadline sits under the interval
and the query time limit under the deadline; the unit carries qv4-."""
import support.jobspec as js


def good(**kw):
    base = dict(name="qv4-gazette-capture", needs="processor", memory_gb=1.5, deadline_s=1800, query_timeout_s=600,
                interval_s=86400)
    base.update(kw)
    return js.JobNeeds(**base)


def test_a_good_declaration_passes():
    assert js.validate(good()) == []
    assert js.validate(good(needs="model-profile", model_profile="qwen3.6-35b-a3b-q4km:2x50k", can_share=True)) == []


def test_each_rule_is_named():
    assert js.validate(good(name="gazette-capture")) == ["a job's unit name carries the qv4- prefix (hard limit 23)"]
    assert js.validate(good(needs="model-profile")) == ["a job that needs a model names its model profile"]
    assert js.validate(good(model_profile="x")) == ["a processor job names no model profile"]
    assert "the deadline must be shorter than the interval" in js.validate(good(deadline_s=86400))
    assert "the query time limit sits under the deadline" in js.validate(good(query_timeout_s=1800))
    assert "memory_gb is measured and positive" in js.validate(good(memory_gb=0))
    assert js.validate(good(interval_s=0)) == []          # on demand: no interval to be under
