# run.py

from src.graph.builder import build_test_graph

# 示例输入文本（包含多个症状）
input_text = "My child has chest pain."

# 初始状态
state = {
    "text": input_text,
    "ontology": "HPO"
}

# 构建图并执行
graph = build_test_graph()
final_state = graph.invoke(state)

# 打印完整状态（可选）
print("\n🎯 Final State:")
for key in ["text", "extracted_terms", "ontology"]:
    print(f"{key}: {final_state.get(key)}")

# 打印验证结果
print("\n✅ Validated Mappings:")
validated = final_state.get("validated_mappings", [])
if not validated:
    print("⚠️ No validated results found.")
else:
    for item in validated:
        print(f"\n🔹 Symptom: {item.get('original')}")
        print(f"   Best Match Term : {item.get('best_match_term')}")
        print(f"   Best Match Code : {item.get('best_match_code')}")
        print(f"   Confidence      : {item.get('confidence'):.0%}")
