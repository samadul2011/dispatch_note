# your_app/management/commands/import_dispatch_details.py
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from dispatch_app.models import DispatchDetails, Dispatch, Products
import openpyxl

class Command(BaseCommand):
    help = 'Import DispatchDetails from Excel file'

    def handle(self, *args, **options):
        excel_file = r"C:\Users\samad\OneDrive - Atyab Food Industries\Documents\DispatchDetails.xlsx"
        
        if not os.path.exists(excel_file):
            self.stdout.write(self.style.ERROR(f"File not found: {excel_file}"))
            return

        try:
            workbook = openpyxl.load_workbook(excel_file)
            sheet = workbook.active  # or use workbook["SheetName"] if needed

            headers = [cell.value for cell in sheet[1]]
            self.stdout.write(f"Headers: {headers}")

            # Expected columns (adjust if your Excel uses different names)
            required_cols = {"DispatchID", "Code", "Qty"}
            missing = required_cols - set(headers)
            if missing:
                self.stdout.write(self.style.ERROR(f"Missing columns: {missing}"))
                return

            created = 0
            updated = 0
            errors = 0

            for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                row_data = dict(zip(headers, row))
                
                # Get required fields
                dispatch_id = row_data.get("DispatchID")
                product_code = row_data.get("Code")
                qty = row_data.get("Qty")

                if not dispatch_id or not product_code or qty is None:
                    self.stdout.write(self.style.WARNING(f"Row {idx}: Missing required data. Skipped."))
                    errors += 1
                    continue

                # 🔍 Resolve Foreign Keys
                try:
                    dispatch = Dispatch.objects.get(DispatchID=dispatch_id)
                    product = Products.objects.get(Code=product_code)
                except Dispatch.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Row {idx}: DispatchID {dispatch_id} not found."))
                    errors += 1
                    continue
                except Products.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Row {idx}: Product Code '{product_code}' not found."))
                    errors += 1
                    continue

                # 🗓️ Parse dates
                def parse_date(val):
                    if val is None:
                        return None
                    if isinstance(val, datetime):
                        return val.date()
                    if isinstance(val, str):
                        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                            try:
                                return datetime.strptime(val, fmt).date()
                            except ValueError:
                                continue
                    return None

                # Prepare data
                detail_data = {
                    "DispatchID": dispatch,
                    "Code": product,
                    "LocalCode": row_data.get("LocalCode") or "",
                    "Description": row_data.get("Description") or "",
                    "UOM": row_data.get("UOM") or "",
                    "PackInCarton": self.to_decimal(row_data.get("PackInCarton")),
                    "Qty": self.to_decimal(qty, max_digits=15, decimal_places=4),
                    "ParPallet": self.to_decimal(row_data.get("ParPallet")),
                    "ProductionDate": parse_date(row_data.get("ProductionDate")),
                    "ExpairyDate": parse_date(row_data.get("ExpairyDate")),
                }

                # 🔄 Create or Update
                # Option A: If Excel has "ID" column → use it
                # Option B: Use natural key (DispatchID + Code) → safer if no ID

                if "ID" in headers and row_data.get("ID"):
                    # Update by ID
                    obj, created_flag = DispatchDetails.objects.update_or_create(
                        ID=row_data["ID"],
                        defaults=detail_data
                    )
                else:
                    # Update by (DispatchID, Code) — prevents duplicates
                    obj, created_flag = DispatchDetails.objects.update_or_create(
                        DispatchID=dispatch,
                        Code=product,
                        defaults=detail_data
                    )

                if created_flag:
                    created += 1
                else:
                    updated += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Import finished!\n"
                    f"Created: {created}\n"
                    f"Updated: {updated}\n"
                    f"Errors: {errors}"
                )
            )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Error: {e}"))

    def to_decimal(self, val, max_digits=10, decimal_places=2):
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None