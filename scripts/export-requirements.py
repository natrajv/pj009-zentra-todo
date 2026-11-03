# Export requirements csv files from Zentra BA report in xlsx
#---
# Version: v1.1.2-20261103_0756
#-----#

from pathlib import Path
import pandas as pd

# Input Excel workbook
workbook = Path(r"D:\Workspace\projects\pj009-zentra-todo\02-ba-zentra-todo-v1.1.0w-20261102_1814.xlsx")

# Output directory for generated CSV files
output_dir = Path("../project-data/generated")

# Map: Excel worksheet name -> output CSV filename
sheet_mapping = {
    "1.1-requirements": "requirements.csv",
    "2-usecases": "use_cases.csv",
    "3.0-product_backlogs": "product_backlog.csv",
    "3.1-sprint_backlogs": "sprint_backlog.csv",
}


def export_worksheets(
    workbook_path: Path,
    output_directory: Path,
    mapping: dict[str, str],
) -> None:
    """Export selected Excel worksheets to CSV files."""

    if not workbook_path.is_file():
        raise FileNotFoundError(
            f"Requirements workbook not found: {workbook_path}"
        )

    output_directory.mkdir(parents=True, exist_ok=True)

    # Read the workbook once and validate worksheet names.
    with pd.ExcelFile(workbook_path) as excel:
        available_sheets = excel.sheet_names

        missing_sheets = [
            sheet
            for sheet in mapping
            if sheet not in available_sheets
        ]

        if missing_sheets:
            raise ValueError(
                f"Missing worksheets: {missing_sheets}. "
                f"Available worksheets: {available_sheets}"
            )

        # Export each mapped worksheet.
        for sheet_name, csv_filename in mapping.items():
            df = pd.read_excel(
                excel,
                sheet_name=sheet_name,
            )

            output_file = output_directory / csv_filename

            df.to_csv(
                output_file,
                index=False,
                encoding="utf-8-sig",
            )

            print(
                f"Exported '{sheet_name}' -> '{output_file}' "
                f"({len(df)} rows)"
            )

    print("All worksheets exported successfully.")


if __name__ == "__main__":
    export_worksheets(
        workbook_path=workbook,
        output_directory=output_dir,
        mapping=sheet_mapping,
    )