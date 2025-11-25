from neo4j import GraphDatabase
from collections import defaultdict

# ========= 1. 配置 Neo4j Aura 连接 =========
# 建议直接复用你前面脚本里的配置
NEO4J_URI = "neo4j+s://36f08b4f.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Z-kmRY5XTupSahevPpRzQZqpRfFcw0ApigFBfDVFyQo"  

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

INFO_TYPE_DEFINITION = "定义"


# ========= 2. 读取 STAGE 对应的【定义】文本 =========
def fetch_stage_definitions(tx):
    """
    返回所有与 STAGE 关联的定义类 TEXT_UNIT：
    (process_name, stage_name) -> 多条 content
    """
    query = """
    MATCH (t:TEXT_UNIT {info_type:$info_type})-[:ABOUT_STAGE]->(s:STAGE)
    RETURN s.process_name AS process_name,
           s.name AS stage_name,
           t.content AS content
    """
    result = tx.run(query, info_type=INFO_TYPE_DEFINITION)
    records = list(result)

    by_stage = defaultdict(list)
    for r in records:
        key = (r["process_name"], r["stage_name"])
        by_stage[key].append(r["content"])
    return by_stage


# ========= 3. 读取 PROCESS 对应的【定义】文本 =========
def fetch_process_definitions(tx):
    """
    返回所有与 PROCESS 关联的定义类 TEXT_UNIT：
    process_name -> 多条 content

    说明：
    文档中目前没有专门“工艺层面”的定义，
    所以这里是把该工艺所有工序的【定义】文本聚合在一起。
    如果你觉得太长，可以后面改成只取一条或人工写。
    """
    query = """
    MATCH (t:TEXT_UNIT {info_type:$info_type})-[:ABOUT_PROCESS]->(p:PROCESS)
    RETURN p.name AS process_name,
           t.content AS content
    """
    result = tx.run(query, info_type=INFO_TYPE_DEFINITION)
    records = list(result)

    by_process = defaultdict(list)
    for r in records:
        key = r["process_name"]
        by_process[key].append(r["content"])
    return by_process


# ========= 4. 写回 STAGE.description =========
def update_stage_descriptions(tx, stage_defs):
    """
    对每个 (process_name, stage_name)，设置：
    s.description = 所有关联定义文本拼接
    """
    for (process_name, stage_name), defs in stage_defs.items():
        description = "\n\n".join(defs).strip()
        tx.run(
            """
            MATCH (s:STAGE {name:$stage_name, process_name:$process_name})
            SET s.description = $description
            """,
            {
                "stage_name": stage_name,
                "process_name": process_name,
                "description": description,
            },
        )


# ========= 5. 写回 PROCESS.description =========
def update_process_descriptions(tx, process_defs):
    """
    对每个 process_name，设置：
    p.description = 该工艺下所有定义文本的拼接

    如果你觉得太长，可以改成：
    - 只取第一条： defs[0]
    - 或者手动写一个更精简的 description 再覆盖。
    """
    for process_name, defs in process_defs.items():
        description = "\n\n".join(defs).strip()
        tx.run(
            """
            MATCH (p:PROCESS {name:$process_name})
            SET p.description = $description
            """,
            {
                "process_name": process_name,
                "description": description,
            },
        )


def main():
    with driver.session() as session:
        # 1. 先把定义文本读出来（读操作）
        stage_defs = session.execute_read(fetch_stage_definitions)
        process_defs = session.execute_read(fetch_process_definitions)

        print(f"将为 {len(stage_defs)} 个 STAGE 写入 description")
        print(f"将为 {len(process_defs)} 个 PROCESS 写入 description")

        # 2. 写回 STAGE.description & PROCESS.description（写操作）
        def _write_all(tx):
            update_stage_descriptions(tx, stage_defs)
            update_process_descriptions(tx, process_defs)

        session.execute_write(_write_all)

    print("基于【定义】TEXT_UNIT 的 description 写回已完成！")


if __name__ == "__main__":
    main()
    driver.close()
