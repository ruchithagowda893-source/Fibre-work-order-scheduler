import csv
from pathlib import Path
from datetime import datetime

try:
    from .utils import read_csv_file, split_values
except ImportError:
    from utils import read_csv_file, split_values


class Scheduler:
    def __init__(self):
        self.zones = {}
        self.technicians = []
        self.work_orders = []
        self.assignments = []
        self.unassigned = []
        self.errors = []
        self.pending = []

    def load_zones(self, file_path):
        rows = read_csv_file(file_path)
        for line_no, row in enumerate(rows, start=2):
            zone_id = row["zone_id"].strip()
            if not zone_id or zone_id in self.zones:
                self.errors.append({
                    "file": "zones.csv",
                    "line_no": line_no,
                    "reason": "INVALID_OR_DUPLICATE_ZONE_ID"
                })
                continue
            self.zones[zone_id] = {
                **row,
                "adjacent_zones": split_values(row["adjacent_zones"])
            }

    def load_technicians(self, file_path):
        rows = read_csv_file(file_path)
        for line_no, row in enumerate(rows, start=2):
            if row["home_zone"] not in self.zones:
                self.errors.append({
                    "file": "technicians.csv",
                    "line_no": line_no,
                    "reason": "UNKNOWN_HOME_ZONE"
                })
                continue

            self.technicians.append({
                **row,
                "skills_list": split_values(row["skills"]),
                "leave_list": split_values(row["leave_dates"]),
                "slots": {}
            })

        self.technicians.sort(key=lambda t: t["technician_id"])

    def load_work_orders(self, file_path):
        rows = read_csv_file(file_path)
        seen_ids = set()

        for line_no, row in enumerate(rows, start=2):
            order_id = row["order_id"].strip()

            if order_id in seen_ids:
                self.errors.append({
                    "file": "work_orders.csv",
                    "line_no": line_no,
                    "reason": "DUPLICATE_ORDER_ID"
                })
                continue

            seen_ids.add(order_id)

            if row["zone_id"] not in self.zones:
                self.errors.append({
                    "file": "work_orders.csv",
                    "line_no": line_no,
                    "reason": "UNKNOWN_ORDER_ZONE"
                })
                continue

            try:
                bumps = int(row["priority_bumps"])
                datetime.strptime(row["requested_date"], "%Y-%m-%d")
            except (ValueError, TypeError):
                self.errors.append({
                    "file": "work_orders.csv",
                    "line_no": line_no,
                    "reason": "INVALID_DATE_OR_PRIORITY"
                })
                continue

            order = {
                **row,
                "priority_bumps": bumps,
                "required_list": split_values(row["required_skills"])
            }
            self.work_orders.append(order)

        self.pending = list(self.work_orders)

    def _priority(self, order):
        order_type = order["order_type"]

        if order_type == "ENTERPRISE":
            group = 0
        elif order_type == "REPAIR" or (
            order_type == "NEW_INSTALL"
            and order["priority_bumps"] >= 2
        ):
            group = 1
        else:
            group = 2

        return (group, order["requested_date"], order["order_id"])

    def _in_range(self, technician, zone_id):
        home = technician["home_zone"]
        if home == zone_id:
            return True
        return zone_id in self.zones[home]["adjacent_zones"]

    def _has_skills(self, technician, order):
        return set(order["required_list"]).issubset(
            set(technician["skills_list"])
        )

    def _duration(self, order):
        return {
            "NEW_INSTALL": 2,
            "REPAIR": 1,
            "ENTERPRISE": 3
        }.get(order["order_type"], 1)

    def _find_slots(self, technician, order):
        zone_id = order["zone_id"]
        adjacent = (
            technician["home_zone"] != zone_id
            and self._in_range(technician, zone_id)
        )

        job_count = self._duration(order)
        total_count = job_count + (1 if adjacent else 0)

        slot_names = ["S1", "S2", "S3", "S4"]

        for start in range(0, 5 - total_count):
            selected = slot_names[start:start + total_count]

            if all(slot not in technician["slots"] for slot in selected):
                job_slots = selected[:job_count]
                travel_slot = selected[-1] if adjacent else "NONE"
                return job_slots, travel_slot

        return None

    def schedule(self, schedule_date):
        datetime.strptime(schedule_date, "%Y-%m-%d")

        for technician in self.technicians:
            technician["slots"] = {}

        candidates = [
            order for order in self.pending
            if order["requested_date"] <= schedule_date
        ]
        candidates.sort(key=self._priority)

        remaining = []
        all_on_leave = bool(self.technicians) and all(
            schedule_date in technician["leave_list"]
            for technician in self.technicians
        )

        for order in candidates:
            reason = None
            selected = None

            if all_on_leave:
                reason = "ALL_ON_LEAVE"
            else:
                skilled_anywhere = [
                    t for t in self.technicians
                    if self._has_skills(t, order)
                ]

                if not skilled_anywhere:
                    reason = "NO_SKILL"
                else:
                    in_range = [
                        t for t in skilled_anywhere
                        if self._in_range(t, order["zone_id"])
                    ]

                    if not in_range:
                        reason = "NO_TECH_IN_RANGE"
                    else:
                        for technician in in_range:
                            if schedule_date in technician["leave_list"]:
                                continue

                            slots = self._find_slots(technician, order)
                            if slots is not None:
                                selected = (technician, slots)
                                break

                        if selected is None:
                            reason = "NO_SLOT"

            if selected:
                technician, (job_slots, travel_slot) = selected

                for slot in job_slots:
                    technician["slots"][slot] = order["order_id"]

                if travel_slot != "NONE":
                    technician["slots"][travel_slot] = "TRAVEL"

                self.assignments.append({
                    "schedule_date": schedule_date,
                    "technician_id": technician["technician_id"],
                    "order_id": order["order_id"],
                    "order_type": order["order_type"],
                    "zone_id": order["zone_id"],
                    "job_slots": ";".join(job_slots),
                    "travel_slot": travel_slot,
                    "overdue": str(
                        order["requested_date"] < schedule_date
                    ).lower()
                })
            else:
                order["priority_bumps"] += 1
                remaining.append(order)

                self.unassigned.append({
                    "schedule_date": schedule_date,
                    "order_id": order["order_id"],
                    "order_type": order["order_type"],
                    "zone_id": order["zone_id"],
                    "reason": reason,
                    "priority_bumps_after": order["priority_bumps"]
                })

        self.pending = remaining

        print(f"\nSchedule for {schedule_date}")
        print(f"Assigned: {len(candidates) - len(remaining)}")
        print(f"Unassigned: {len(remaining)}")

    def export_reports(self, output_dir):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        reports = {
            "assignments.csv": (
                self.assignments,
                [
                    "schedule_date", "technician_id", "order_id",
                    "order_type", "zone_id", "job_slots",
                    "travel_slot", "overdue"
                ]
            ),
            "unassigned.csv": (
                self.unassigned,
                [
                    "schedule_date", "order_id", "order_type",
                    "zone_id", "reason", "priority_bumps_after"
                ]
            ),
            "errors.csv": (
                self.errors,
                ["file", "line_no", "reason"]
            )
        }

        for filename, (rows, columns) in reports.items():
            if filename == "assignments.csv":
                rows.sort(key=lambda r: (
                    r["schedule_date"],
                    r["technician_id"],
                    r["job_slots"].split(";")[0]
                ))

            with open(
                output_dir / filename,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:
                writer = csv.DictWriter(file, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)

            print(f"Created: {filename}")