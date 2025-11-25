# Car-GraphRAG
该项目旨在构建汽车工业领域知识图谱，通过GraphRAG实现专家问答，为LLM决策提供支撑，最终实现汽车产线自动化
## 知识文档
汽车领域知识文档多为内部资料，不易搜集，因此在已有资料基础上进行ai扩展，具体内容参考“汽车工业产线知识文档.txt”
## 知识图谱构建
本项目主要采用GraphRAG中BYOG（Bring Your Own Graph）方案，手动创建知识图谱，具体代码参考“create graph”，构建结果如下图所示
<img width="603" height="588" alt="image" src="https://github.com/user-attachments/assets/bdc59d64-79ce-4453-97e8-0b72afd1fdbf" />
## 本地部署
### one-api搭建
配置好大模型API KEY后打开本地端口  
### 知识图谱导出
配置neo4j链接，导出.parquet格式文件供GraphRAG还原图结构和查询
### 构建索引
python -m graphrag.index --root .  <br>
执行后GraphRAG会对text_unit进行embedding，并进行聚类得到community
### 进行检索
本项目采用了服务器-客户端的方式，也可直接调用GraphRAG官方提供的调试入口，代码如下 <br>
python -m graphrag.query --root .  <br> 
主流查询方式分为Global Search和Local Search，前者适合全局性问答，后者适合细节性问答

本项目参考了B站up主的视频，其主页如下：https://space.bilibili.com/3546860755093522/?spm_id_from=333.788.upinfo.head.click
