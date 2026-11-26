from pathlib import Path
from scheduler import Scheduler


def main():
    project_dir = Path(__file__).resolve().parent.parent
    data_dir = project_dir / "data"
    output_dir = project_dir / "outputs"

    scheduler = Scheduler()

    print("===================================")
    print(" FIBRE INSTALLATION SCHEDULER")
    print("===================================")
    print("Project: E031-ECE-009")
    print("Starting scheduling engine...")

    commands_file = data_dir / "commands.txt"

    with open(commands_file, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split("|")
            command = parts[0].strip()

            if command == "LOAD_ZONES":
                scheduler.load_zones(data_dir / parts[1].strip())
                print("Zones loaded.")

            elif command == "LOAD_TECHNICIANS":
                scheduler.load_technicians(data_dir / parts[1].strip())
                print("Technicians loaded.")

            elif command == "LOAD_WORK_ORDERS":
                scheduler.load_work_orders(data_dir / parts[1].strip())
                print("Work orders loaded.")

            elif command == "SCHEDULE":
                scheduler.schedule(parts[1].strip())

            else:
                print(f"Unknown command: {command}")

    scheduler.export_reports(output_dir)

    print("\nScheduling completed.")
    print(f"Reports saved in: {output_dir}")


if __name__ == "__main__":
    main()