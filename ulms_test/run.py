from src.graph.builder import build_graph

if __name__ == "__main__":
    graph = build_graph()

    # 测试输入文本
    test_state = {
        "text": "Does your child have chest pain?",
        "ontology": "HPO"
    }

    print("🚀 Running full symptom mapping graph...\n")
    final_state = graph.invoke(test_state)

    print("\n🎯 Final Output State:")
    print(final_state)