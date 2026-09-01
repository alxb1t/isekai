import copy
import random

import pytest

from isekai.comfy_types import Workflow
from isekai.mutate import mutate


@pytest.mark.spec("workflow-mutation:jitter:seed-comes-from-the-rng")
def test_mutate_sets_the_ksampler_seed_from_the_rng(
    animagine_i2i_workflow: Workflow,
) -> None:
    mutate(animagine_i2i_workflow, random.Random(0))
    assert animagine_i2i_workflow["10"]["inputs"]["seed"] == random.Random(
        0
    ).getrandbits(64)


@pytest.mark.spec("workflow-mutation:jitter:seed-is-64-bit")
def test_mutate_draws_a_64_bit_seed(animagine_i2i_workflow: Workflow) -> None:
    mutate(animagine_i2i_workflow, random.Random(1))
    assert 0 <= animagine_i2i_workflow["10"]["inputs"]["seed"] < 2**64


@pytest.mark.spec("workflow-mutation:jitter:denoise-within-band")
def test_mutate_jitters_denoise_within_range(animagine_i2i_workflow: Workflow) -> None:
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 0.60 <= wf["10"]["inputs"]["denoise"] <= 0.70


@pytest.mark.spec("workflow-mutation:jitter:cfg-within-band")
def test_mutate_jitters_cfg_within_range(animagine_i2i_workflow: Workflow) -> None:
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 4.5 <= wf["10"]["inputs"]["cfg"] <= 5.5


@pytest.mark.spec("workflow-mutation:jitter:ip-weight-within-band")
def test_mutate_jitters_ip_weight_within_range(
    animagine_i2i_workflow: Workflow,
) -> None:
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 0.85 <= wf["8"]["inputs"]["ip_weight"] <= 0.95


@pytest.mark.spec("workflow-mutation:reproducibility:same-seed-same-result")
def test_mutate_is_reproducible_for_the_same_seed(
    animagine_i2i_workflow: Workflow,
) -> None:
    a = copy.deepcopy(animagine_i2i_workflow)
    b = copy.deepcopy(animagine_i2i_workflow)
    mutate(a, random.Random(42))
    mutate(b, random.Random(42))
    assert a == b


@pytest.mark.spec("workflow-mutation:reproducibility:distinct-states-diverge")
def test_mutate_differs_for_distinct_rng_states(
    animagine_i2i_workflow: Workflow,
) -> None:
    a = copy.deepcopy(animagine_i2i_workflow)
    b = copy.deepcopy(animagine_i2i_workflow)
    mutate(a, random.Random(1))
    mutate(b, random.Random(2))
    assert a["10"]["inputs"]["seed"] != b["10"]["inputs"]["seed"]


@pytest.mark.spec("workflow-mutation:controlnet:strengths-are-jittered")
def test_mutate_jitters_the_controlnet_strenghts(
    animagine_i2i_cn_workflow: Workflow,
) -> None:
    before = {
        nid: n["inputs"]["strength"]
        for nid, n in animagine_i2i_cn_workflow.items()
        if n["class_type"] == "ControlNetApplyAdvanced"
    }
    assert before

    wf = copy.deepcopy(animagine_i2i_cn_workflow)
    mutate(wf, random.Random(3))
    after = {nid: wf[nid]["inputs"]["strength"] for nid in before}

    assert after != before
    for nid, base in before.items():
        # Per node, not just over the dict: a whole-dict comparison passes when
        # only one of the three ControlNets moved, leaving the rest frozen.
        assert after[nid] != base
        assert max(0.0, base - 0.1) <= after[nid] <= min(1.0, base + 0.1)


@pytest.mark.spec("workflow-mutation:controlnet:strengths-stay-in-band")
def test_mutate_keeps_every_controlnet_strength_in_its_band(
    animagine_i2i_cn_workflow: Workflow,
) -> None:
    bases = {
        nid: n["inputs"]["strength"]
        for nid, n in animagine_i2i_cn_workflow.items()
        if n["class_type"] == "ControlNetApplyAdvanced"
    }
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_cn_workflow)
        mutate(wf, random.Random(i))
        for nid, base in bases.items():
            s = wf[nid]["inputs"]["strength"]
            assert max(0.0, base - 0.1) <= s <= min(1.0, base + 0.1)


@pytest.mark.spec("workflow-mutation:controlnet:reproducible-from-seed")
def test_mutate_in_reproducible_on_the_controlnet_path(
    animagine_i2i_cn_workflow: Workflow,
) -> None:
    a = copy.deepcopy(animagine_i2i_cn_workflow)
    b = copy.deepcopy(animagine_i2i_cn_workflow)
    mutate(a, random.Random(7))
    mutate(b, random.Random(7))
    assert a == b


# --- Phase 1: base-relative jitter ---


@pytest.mark.spec("workflow-mutation:controlnet:no-draw-without-controlnet-nodes")
def test_mutate_with_baked_defaults_reproduces_today_output(
    animagine_i2i_workflow: Workflow,
) -> None:
    mutate(animagine_i2i_workflow, random.Random(99))
    assert animagine_i2i_workflow["10"]["inputs"]["seed"] == 7023646418445998953
    assert animagine_i2i_workflow["10"]["inputs"]["denoise"] == 0.6200075444574945
    assert animagine_i2i_workflow["10"]["inputs"]["cfg"] == 4.6788023205866125
    assert animagine_i2i_workflow["8"]["inputs"]["ip_weight"] == 0.8748431318500969


@pytest.mark.spec("workflow-mutation:base-relative:denoise-around-current-base")
def test_mutate_jitters_denoise_around_its_current_base(
    animagine_i2i_workflow: Workflow,
) -> None:
    animagine_i2i_workflow["10"]["inputs"]["denoise"] = 0.70
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 0.65 <= wf["10"]["inputs"]["denoise"] <= 0.75


@pytest.mark.spec("workflow-mutation:base-relative:cfg-around-current-base")
def test_mutate_jitters_cfg_around_its_current_base(
    animagine_i2i_workflow: Workflow,
) -> None:
    animagine_i2i_workflow["10"]["inputs"]["cfg"] = 6.0
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 5.5 <= wf["10"]["inputs"]["cfg"] <= 6.5


@pytest.mark.spec("workflow-mutation:base-relative:ip-weight-around-current-base")
def test_mutate_jitters_ip_weight_around_its_current_base(
    animagine_i2i_workflow: Workflow,
) -> None:
    animagine_i2i_workflow["8"]["inputs"]["ip_weight"] = 0.80
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 0.75 <= wf["8"]["inputs"]["ip_weight"] <= 0.85


# --- Clamp boundaries -------------------------------------------------------
# Every fixture base and every base-relative test above sits strictly interior,
# so `min(hi, max(lo, ...))` never fires and dropping it keeps the suite green.
# These pin the boundaries the CLI explicitly accepts.


@pytest.mark.spec("workflow-mutation:jitter:denoise-within-band")
def test_mutate_clamps_denoise_at_the_top_of_its_range(
    animagine_i2i_workflow: Workflow,
) -> None:
    animagine_i2i_workflow["10"]["inputs"]["denoise"] = 1.0
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 0.0 <= wf["10"]["inputs"]["denoise"] <= 1.0


@pytest.mark.spec("workflow-mutation:jitter:denoise-within-band")
def test_mutate_clamps_denoise_at_the_bottom_of_its_range(
    animagine_i2i_workflow: Workflow,
) -> None:
    animagine_i2i_workflow["10"]["inputs"]["denoise"] = 0.0
    for i in range(100):
        wf = copy.deepcopy(animagine_i2i_workflow)
        mutate(wf, random.Random(i))
        assert 0.0 <= wf["10"]["inputs"]["denoise"] <= 1.0


@pytest.mark.spec("workflow-mutation:jitter:cfg-within-band")
def test_mutate_clamps_cfg_at_the_edges_of_its_range(
    animagine_i2i_workflow: Workflow,
) -> None:
    for base in (0.0, 30.0):
        animagine_i2i_workflow["10"]["inputs"]["cfg"] = base
        for i in range(100):
            wf = copy.deepcopy(animagine_i2i_workflow)
            mutate(wf, random.Random(i))
            assert 0.0 <= wf["10"]["inputs"]["cfg"] <= 30.0


@pytest.mark.spec("workflow-mutation:jitter:ip-weight-within-band")
def test_mutate_clamps_ip_weight_at_the_edges_of_its_range(
    animagine_i2i_workflow: Workflow,
) -> None:
    for base in (0.0, 1.0):
        animagine_i2i_workflow["8"]["inputs"]["ip_weight"] = base
        for i in range(100):
            wf = copy.deepcopy(animagine_i2i_workflow)
            mutate(wf, random.Random(i))
            assert 0.0 <= wf["8"]["inputs"]["ip_weight"] <= 1.0


@pytest.mark.spec("workflow-mutation:controlnet:strengths-stay-in-band")
def test_mutate_clamps_controlnet_strengths_at_the_edges(
    animagine_i2i_cn_workflow: Workflow,
) -> None:
    cn_ids = [
        nid
        for nid, n in animagine_i2i_cn_workflow.items()
        if n["class_type"] == "ControlNetApplyAdvanced"
    ]
    assert cn_ids
    for base in (0.0, 1.0):
        for nid in cn_ids:
            animagine_i2i_cn_workflow[nid]["inputs"]["strength"] = base
        for i in range(100):
            wf = copy.deepcopy(animagine_i2i_cn_workflow)
            mutate(wf, random.Random(i))
            for nid in cn_ids:
                assert 0.0 <= wf[nid]["inputs"]["strength"] <= 1.0


@pytest.mark.spec("workflow-mutation:jitter:linked-dial-refused-legibly")
def test_mutate_refuses_a_dial_wired_to_another_node(qwen_workflow: Workflow) -> None:
    # In ComfyUI API format an input may legally be a [node_id, slot] link rather
    # than a scalar -- qwen-image-edit.json drives cfg from a Switch node. Since
    # v0.6 made the jitter base-relative, mutate READS the dial, so such a graph
    # must stop legibly instead of raising a raw TypeError from the arithmetic.
    with pytest.raises(SystemExit) as exit_info:
        mutate(qwen_workflow, random.Random(1))

    message = str(exit_info.value)
    assert "cfg" in message
    assert "102:109" in message


@pytest.mark.spec("workflow-mutation:jitter:linked-dial-refused-legibly")
@pytest.mark.parametrize("bad", [None, {"nested": 1}, "0.65", []])
def test_mutate_refuses_any_non_numeric_dial_without_crashing(bad: object) -> None:
    # The guard must not reach for value[0] unconditionally: a null or an object
    # would then raise the raw TypeError/KeyError the guard exists to replace.
    wf = {"10": {"class_type": "KSampler", "inputs": {"seed": 0, "denoise": bad}}}
    with pytest.raises(SystemExit) as exit_info:
        mutate(wf, random.Random(1))
    assert "denoise" in str(exit_info.value)


@pytest.mark.spec("workflow-mutation:controlnet:strengths-are-jittered")
def test_mutate_handles_subgraph_style_controlnet_node_ids() -> None:
    # ComfyUI subgraph exports use "102:14"-style ids -- qwen-image-edit.json
    # already ships them -- and find_node handles those fine, so nothing else in
    # the codebase signals that node ids must be integers.
    wf: Workflow = {
        "102:3": {
            "class_type": "KSampler",
            "inputs": {"seed": 0, "denoise": 0.65, "cfg": 5.0},
        },
        "102:8": {"class_type": "ApplyInstantIDAdvanced", "inputs": {"ip_weight": 0.9}},
        "102:14": {
            "class_type": "ControlNetApplyAdvanced",
            "inputs": {"strength": 0.6},
        },
        "102:2": {"class_type": "ControlNetApplyAdvanced", "inputs": {"strength": 0.2}},
    }
    mutate(wf, random.Random(5))
    for nid in ("102:14", "102:2"):
        assert 0.0 <= wf[nid]["inputs"]["strength"] <= 1.0


@pytest.mark.spec("workflow-mutation:controlnet:reproducible-from-seed")
def test_mutate_pins_each_controlnet_strength_for_a_fixed_seed(
    animagine_i2i_cn_workflow: Workflow,
) -> None:
    # Comparing two mutations of the same dict shares one iteration order by
    # construction, so it cannot detect order-dependence. Pin the actual values:
    # the node sort is the only thing making seed -> strength canonical, and a
    # re-export of the workflow JSON in a different node order must not silently
    # change what a given seed renders.
    mutate(animagine_i2i_cn_workflow, random.Random(3))
    assert animagine_i2i_cn_workflow["14"]["inputs"]["strength"] == 0.22514406082161081
    assert animagine_i2i_cn_workflow["18"]["inputs"]["strength"] == 0.5131057718479626
    assert animagine_i2i_cn_workflow["21"]["inputs"]["strength"] == 0.10263359831097484


@pytest.mark.spec("workflow-mutation:controlnet:reproducible-from-seed")
def test_mutate_draws_controlnet_strengths_in_numeric_node_order() -> None:
    # The shipped fixture's ids ("14", "18", "21") sort the same lexicographically
    # as numerically, so it cannot tell a numeric sort from a plain one -- or from
    # no sort at all. These ids diverge: numerically 2 < 10, lexicographically
    # "10" < "2". Pinning them is what makes the node ordering, and therefore the
    # seed -> strength mapping, actually load-bearing.
    wf: Workflow = {
        "1": {
            "class_type": "KSampler",
            "inputs": {"seed": 0, "denoise": 0.65, "cfg": 5.0},
        },
        "3": {"class_type": "ApplyInstantIDAdvanced", "inputs": {"ip_weight": 0.9}},
        "10": {"class_type": "ControlNetApplyAdvanced", "inputs": {"strength": 0.20}},
        "2": {"class_type": "ControlNetApplyAdvanced", "inputs": {"strength": 0.60}},
    }
    mutate(wf, random.Random(3))
    assert wf["2"]["inputs"]["strength"] == 0.6251440608216108
    assert wf["10"]["inputs"]["strength"] == 0.11310577184796262


@pytest.mark.spec("workflow-mutation:controlnet:reproducible-from-seed")
def test_mutate_is_independent_of_the_json_node_order(
    animagine_i2i_cn_workflow: Workflow,
) -> None:
    # The golden above cannot catch a DROPPED sort key, because the shipped
    # fixture already happens to be stored in ascending order. This builds the
    # same graph with the node keys inserted in reverse and asserts the same seed
    # still yields the same strengths -- which is precisely what survives a
    # re-export of the workflow JSON from ComfyUI.
    shuffled = {
        nid: animagine_i2i_cn_workflow[nid]
        for nid in reversed(list(animagine_i2i_cn_workflow))
    }
    a = copy.deepcopy(animagine_i2i_cn_workflow)
    b = copy.deepcopy(shuffled)
    mutate(a, random.Random(3))
    mutate(b, random.Random(3))

    cn = [nid for nid, n in a.items() if n["class_type"] == "ControlNetApplyAdvanced"]
    assert cn
    for nid in cn:
        assert a[nid]["inputs"]["strength"] == b[nid]["inputs"]["strength"]
