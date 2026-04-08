#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本

用于初始化 SQLite 数据库，创建表结构并导入示例数据。
可以作为独立脚本运行，也可以在应用启动时自动执行。
"""

import os
import sys
import sqlite3
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from database import Base, engine
from models import (
    FinnhubCache,
    AnalysisReport,
    AgentReport,
    PortfolioHolding,
    AnalysisTask
)
from config import config


def init_database():
    """初始化数据库"""
    print("📦 正在初始化数据库...")

    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表结构创建成功")

        # 导入示例数据
        import_example_data()
        print("✅ 示例数据导入成功")

        print("\n🎉 数据库初始化完成！")
        print(f"📊 数据库文件位置: {config.DATA_DIR / 'finance_assistant.db'}")
        print("\n📝 数据库包含以下表:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise


def import_example_data():
    """导入示例数据"""
    print("📥 正在导入示例数据...")

    # 检查示例数据文件是否存在
    example_sql_file = Path(__file__).parent / "example_data.sql"
    if not example_sql_file.exists():
        print("⚠️  示例数据文件不存在，跳过导入")
        create_sample_portfolio_data()
        return

    try:
        # 直接使用 SQLite 连接执行 SQL 文件
        db_path = config.DATA_DIR / "finance_assistant.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 读取并执行 SQL 文件
        with open(example_sql_file, "r", encoding="utf-8") as f:
            sql_content = f.read()

        # 执行 SQL
        cursor.executescript(sql_content)
        conn.commit()
        conn.close()

        print(f"✅ 示例数据导入成功（{example_sql_file}）")

    except Exception as e:
        print(f"⚠️  示例数据导入失败: {e}")
        # 尝试创建默认的持仓数据
        create_sample_portfolio_data()


def create_sample_portfolio_data():
    """创建示例持仓数据"""
    print("📝 正在创建示例持仓数据...")

    from database import get_db
    from models import PortfolioHolding

    db = next(get_db())

    # 检查是否已存在数据
    existing_data = db.query(PortfolioHolding).first()
    if existing_data:
        print("ℹ️  数据库已包含持仓数据，跳过创建示例数据")
        return

    # 创建示例持仓
    sample_holdings = [
        PortfolioHolding(
            ticker="AAPL",
            quantity=500,
            cost_price=150.0,
            note="苹果公司股票"
        ),
        PortfolioHolding(
            ticker="NVDA",
            quantity=5,
            cost_price=800.0,
            note="英伟达 - AI 赛道"
        ),
        PortfolioHolding(
            ticker="TSLA",
            quantity=3,
            cost_price=200.0,
            note="特斯拉 - 电动车"
        ),
        PortfolioHolding(
            ticker="INTC",
            quantity=1111,
            cost_price=111.0,
            note="英特尔 - 芯片制造"
        )
    ]

    db.add_all(sample_holdings)
    db.commit()
    print(f"✅ 创建了 {len(sample_holdings)} 条示例持仓数据")


def reset_database():
    """重置数据库（删除所有数据和表）"""
    print("⚠️  正在重置数据库...")

    confirm = input("警告: 这将删除所有数据库数据并重置表结构。\n是否继续? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ 操作取消")
        return

    try:
        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        print("✅ 数据库表已删除")

        # 重新创建表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表结构重新创建")

        # 导入示例数据
        import_example_data()
        print("✅ 数据库已重置")

    except Exception as e:
        print(f"❌ 数据库重置失败: {e}")
        raise


def main():
    """主函数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "reset":
            reset_database()
        elif sys.argv[1] == "init":
            init_database()
        elif sys.argv[1] == "sample":
            create_sample_portfolio_data()
        else:
            print("用法: python init_db.py [命令]")
            print("命令:")
            print("  init    - 初始化数据库（创建表结构并导入示例数据）")
            print("  reset   - 重置数据库（删除所有数据并重新初始化）")
            print("  sample  - 仅创建示例持仓数据")
    else:
        # 默认执行初始化
        init_database()


if __name__ == "__main__":
    main()
