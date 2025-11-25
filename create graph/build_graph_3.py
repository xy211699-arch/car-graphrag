from neo4j import GraphDatabase

# ========= 1. 配置 Neo4j Aura 连接 =========

NEO4J_URI = "neo4j+s://36f08b4f.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Z-kmRY5XTupSahevPpRzQZqpRfFcw0ApigFBfDVFyQo"  

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# ========= 2. 每个工艺下工序的顺序（完全按你的语义手工指定） =========
PROCESS_STAGE_ORDER = {
    "冲压工艺": [
        "材料准备",
        "模具安装与调试",
        "冲压成形",
        "修边冲孔",
        "取出与堆垛",
        "质量检验",
    ],
    "焊接工艺": [
        "零件预处理",
        "夹具装夹与定位",
        "点焊/弧焊/激光焊接",
        "焊后整形与清理",
        "质量检验",
    ],
    "涂装工艺": [
        "前处理（清洗/磷化）",
        "电泳涂装（阴极电泳）",
        "中涂与面漆喷涂",
        "烘烤与冷却",
        "返修与打磨抛光",
        "质量检验",
    ],
    "总装工艺": [
        "车身接收与门盖拆卸",
        "一次内饰安装",
        "底盘与动力总成安装",
        "二次内饰及电气装配",
        "外饰件安装",
        "液体加注与功能检测",
        "整车检测",
    ],
}


def set_order_for_process(tx, process_name, stage_names):
    """
    为某一个工艺，按给定 stage_names 顺序：
    - 设置 STAGE.seq_index
    - 建立 STAGE-[:PRECEDES]->下一个 STAGE
    """
    # 可选：先删除该工艺下已有的 PRECEDES 关系，避免历史残留
    tx.run(
        """
        MATCH (p:PROCESS {name:$process})
              -[:HAS_STAGE]->(s1:STAGE)-[r:PRECEDES]->(s2:STAGE)
        DELETE r
        """,
        {"process": process_name},
    )

    for idx, stage_name in enumerate(stage_names):
        # 设置 seq_index
        tx.run(
            """
            MATCH (s:STAGE {name:$stage_name, process_name:$process})
            SET s.seq_index = $idx
            """,
            {"stage_name": stage_name, "process": process_name, "idx": idx},
        )

        # 建立 PRECEDES 到下一步（如果有）
        if idx < len(stage_names) - 1:
            next_stage_name = stage_names[idx + 1]
            tx.run(
                """
                MATCH (s1:STAGE {name:$stage_name, process_name:$process})
                MATCH (s2:STAGE {name:$next_stage_name, process_name:$process})
                MERGE (s1)-[:PRECEDES]->(s2)
                """,
                {
                    "stage_name": stage_name,
                    "next_stage_name": next_stage_name,
                    "process": process_name,
                },
            )


def main():
    with driver.session() as session:
        def _write_all(tx):
            for process_name, stages in PROCESS_STAGE_ORDER.items():
                print(f"正在处理工艺：{process_name}")
                set_order_for_process(tx, process_name, stages)
        session.execute_write(_write_all)

    print("所有工艺的工序顺序（seq_index 和 PRECEDES）已设置完成！")


if __name__ == "__main__":
    main()
    driver.close()
