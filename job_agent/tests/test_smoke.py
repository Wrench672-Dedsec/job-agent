from app.graph.graph import build_graph


def test_graph_smoke():
    graph = build_graph()
    state = {
        "resume_text": "Built a model in Python",
        "jd_text": "Equity research role in Shanghai",
        "target_city": "Shanghai",
        "target_sector": "healthcare",
    }
    result = graph.invoke(state)
    assert "final_report" in result
    assert "jd_profile" in result
