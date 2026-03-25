from db.migration import check_and_migrate_db, main

__all__ = ["check_and_migrate_db", "main"]


if __name__ == "__main__":
    main()