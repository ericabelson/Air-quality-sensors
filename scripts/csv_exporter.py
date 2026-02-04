#!/usr/bin/env python3
"""
CSV Exporter for Dog Bark and Bird Detection Data
==================================================

Generates enhanced CSV reports with:
- Bark events grouped by 5-minute gaps
- Bark events grouped by 10-minute gaps
- Bird detection events
- Daily statistics and summaries
- Excel-compatible formatting

Author: Claude Code
License: MIT
"""

import os
import sys
import csv
import json
from datetime import datetime, timedelta
from collections import defaultdict
import logging

# Configuration
BASE_DIR = os.path.expanduser("~/audio_detection")
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_EXPORT_DIR = os.path.join(BASE_DIR, "csv_exports")
BIRDNET_DB = os.path.expanduser("~/BirdNET-Pi/scripts/birds.db")

# Create export directory
os.makedirs(CSV_EXPORT_DIR, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CSV GENERATION
# ============================================================================

class CSVExporter:
    """Exports detection data to CSV files"""

    def __init__(self):
        self.csv_export_dir = CSV_EXPORT_DIR
        self.data_dir = DATA_DIR

    def export_bark_events_5min(self, output_file=None):
        """
        Export bark events with 5-minute gap grouping

        CSV Format:
        date,start_time,end_time,duration_minutes,max_decibels,num_barks
        """
        if output_file is None:
            output_file = os.path.join(
                self.csv_export_dir,
                f"bark_events_5min_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

        source_file = os.path.join(self.data_dir, "bark_events_5min.csv")

        if not os.path.exists(source_file):
            logger.warning(f"Source file not found: {source_file}")
            return None

        # Copy and enhance
        self._copy_and_enhance_csv(source_file, output_file, gap_type="5min")
        logger.info(f"Exported 5-minute bark events to: {output_file}")
        return output_file

    def export_bark_events_10min(self, output_file=None):
        """
        Export bark events with 10-minute gap grouping

        CSV Format:
        date,start_time,end_time,duration_minutes,max_decibels,num_barks
        """
        if output_file is None:
            output_file = os.path.join(
                self.csv_export_dir,
                f"bark_events_10min_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

        source_file = os.path.join(self.data_dir, "bark_events_10min.csv")

        if not os.path.exists(source_file):
            logger.warning(f"Source file not found: {source_file}")
            return None

        # Copy and enhance
        self._copy_and_enhance_csv(source_file, output_file, gap_type="10min")
        logger.info(f"Exported 10-minute bark events to: {output_file}")
        return output_file

    def _copy_and_enhance_csv(self, source_file, output_file, gap_type):
        """Copy CSV and add additional calculated columns"""
        with open(source_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames + ['day_of_week', 'hour_of_day']

            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                # Add day of week
                date_obj = datetime.strptime(row['date'], '%Y-%m-%d')
                row['day_of_week'] = date_obj.strftime('%A')

                # Add hour of day from start time
                start_time = row['start_time']
                hour = int(start_time.split(':')[0])
                row['hour_of_day'] = hour

                writer.writerow(row)

    def export_bird_detections(self, output_file=None, days=7):
        """
        Export bird detection events from BirdNET-Pi database

        CSV Format:
        date,time,species,common_name,confidence,latitude,longitude
        """
        if output_file is None:
            output_file = os.path.join(
                self.csv_export_dir,
                f"bird_detections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

        # Check if BirdNET database exists
        if not os.path.exists(BIRDNET_DB):
            logger.warning(f"BirdNET database not found: {BIRDNET_DB}")
            return None

        try:
            import sqlite3

            conn = sqlite3.connect(BIRDNET_DB)
            cursor = conn.cursor()

            # Query detections from last N days
            query = """
                SELECT
                    Date,
                    Time,
                    Sci_Name,
                    Com_Name,
                    Confidence,
                    Lat,
                    Lon
                FROM detections
                WHERE Date >= date('now', '-{} days')
                ORDER BY Date DESC, Time DESC
            """.format(days)

            cursor.execute(query)
            rows = cursor.fetchall()

            # Write to CSV
            with open(output_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['date', 'time', 'scientific_name', 'common_name',
                               'confidence', 'latitude', 'longitude'])

                for row in rows:
                    writer.writerow(row)

            conn.close()

            logger.info(f"Exported {len(rows)} bird detections to: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Error exporting bird detections: {e}")
            return None

    def generate_daily_summary(self, date=None, output_file=None):
        """
        Generate daily summary report

        CSV Format:
        metric,value
        date,YYYY-MM-DD
        total_bark_events_5min,N
        total_bark_events_10min,N
        total_barking_duration_5min,N minutes
        total_barking_duration_10min,N minutes
        max_decibels,N dB
        avg_decibels,N dB
        total_bird_species,N
        total_bird_detections,N
        most_common_bird,Species Name
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        if output_file is None:
            output_file = os.path.join(
                self.csv_export_dir,
                f"daily_summary_{date}.csv"
            )

        summary = {
            'date': date,
            'total_bark_events_5min': 0,
            'total_bark_events_10min': 0,
            'total_barking_duration_5min': 0,
            'total_barking_duration_10min': 0,
            'max_decibels': 0,
            'avg_decibels': 0,
            'total_bird_species': 0,
            'total_bird_detections': 0,
            'most_common_bird': 'N/A'
        }

        # Process 5-min bark events
        file_5min = os.path.join(self.data_dir, "bark_events_5min.csv")
        if os.path.exists(file_5min):
            with open(file_5min, 'r') as f:
                reader = csv.DictReader(f)
                decibels_list = []
                for row in reader:
                    if row['date'] == date:
                        summary['total_bark_events_5min'] += 1
                        summary['total_barking_duration_5min'] += float(row['duration_minutes'])
                        db = float(row['max_decibels'])
                        decibels_list.append(db)
                        summary['max_decibels'] = max(summary['max_decibels'], db)

                if decibels_list:
                    summary['avg_decibels'] = sum(decibels_list) / len(decibels_list)

        # Process 10-min bark events
        file_10min = os.path.join(self.data_dir, "bark_events_10min.csv")
        if os.path.exists(file_10min):
            with open(file_10min, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['date'] == date:
                        summary['total_bark_events_10min'] += 1
                        summary['total_barking_duration_10min'] += float(row['duration_minutes'])

        # Process bird detections
        if os.path.exists(BIRDNET_DB):
            try:
                import sqlite3
                conn = sqlite3.connect(BIRDNET_DB)
                cursor = conn.cursor()

                # Count species
                cursor.execute("""
                    SELECT COUNT(DISTINCT Com_Name)
                    FROM detections
                    WHERE Date = ?
                """, (date,))
                summary['total_bird_species'] = cursor.fetchone()[0]

                # Count total detections
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM detections
                    WHERE Date = ?
                """, (date,))
                summary['total_bird_detections'] = cursor.fetchone()[0]

                # Most common bird
                cursor.execute("""
                    SELECT Com_Name, COUNT(*) as count
                    FROM detections
                    WHERE Date = ?
                    GROUP BY Com_Name
                    ORDER BY count DESC
                    LIMIT 1
                """, (date,))
                result = cursor.fetchone()
                if result:
                    summary['most_common_bird'] = result[0]

                conn.close()
            except Exception as e:
                logger.error(f"Error processing bird data: {e}")

        # Write summary to CSV
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['metric', 'value'])
            for key, value in summary.items():
                writer.writerow([key, value])

        logger.info(f"Generated daily summary: {output_file}")
        return output_file

    def generate_weekly_report(self, output_file=None):
        """Generate weekly report combining all data"""
        if output_file is None:
            output_file = os.path.join(
                self.csv_export_dir,
                f"weekly_report_{datetime.now().strftime('%Y%m%d')}.csv"
            )

        # Get last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        daily_summaries = []
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            summary_file = self.generate_daily_summary(date=date_str)

            if summary_file and os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    reader = csv.DictReader(f)
                    summary = {row['metric']: row['value'] for row in reader}
                    daily_summaries.append(summary)

            current_date += timedelta(days=1)

        # Write weekly report
        if daily_summaries:
            with open(output_file, 'w', newline='') as csvfile:
                fieldnames = daily_summaries[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(daily_summaries)

            logger.info(f"Generated weekly report: {output_file}")
            return output_file

        return None

    def export_all(self):
        """Export all CSV files"""
        logger.info("Exporting all CSV files...")

        files = {
            '5min_events': self.export_bark_events_5min(),
            '10min_events': self.export_bark_events_10min(),
            'bird_detections': self.export_bird_detections(),
            'daily_summary': self.generate_daily_summary(),
            'weekly_report': self.generate_weekly_report()
        }

        logger.info("Export complete!")
        for name, filepath in files.items():
            if filepath:
                logger.info(f"  {name}: {filepath}")

        return files

# ============================================================================
# STATISTICS ANALYZER
# ============================================================================

class StatisticsAnalyzer:
    """Analyzes detection data and generates statistics"""

    def __init__(self):
        self.data_dir = DATA_DIR

    def analyze_bark_patterns(self):
        """Analyze bark patterns and return insights"""
        insights = {
            'peak_hours': [],
            'quietest_hours': [],
            'avg_duration_5min': 0,
            'avg_duration_10min': 0,
            'longest_event': None,
            'total_events': 0
        }

        # Analyze 5-min events
        file_5min = os.path.join(self.data_dir, "bark_events_5min.csv")
        if os.path.exists(file_5min):
            hourly_counts = defaultdict(int)
            durations = []

            with open(file_5min, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    insights['total_events'] += 1

                    # Extract hour
                    hour = int(row['start_time'].split(':')[0])
                    hourly_counts[hour] += 1

                    # Track durations
                    duration = float(row['duration_minutes'])
                    durations.append(duration)

                    # Track longest event
                    if insights['longest_event'] is None or duration > insights['longest_event']['duration']:
                        insights['longest_event'] = {
                            'date': row['date'],
                            'start_time': row['start_time'],
                            'duration': duration
                        }

            # Calculate averages
            if durations:
                insights['avg_duration_5min'] = sum(durations) / len(durations)

            # Find peak and quietest hours
            if hourly_counts:
                sorted_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)
                insights['peak_hours'] = [f"{h:02d}:00" for h, _ in sorted_hours[:3]]
                insights['quietest_hours'] = [f"{h:02d}:00" for h, _ in sorted_hours[-3:]]

        return insights

    def print_statistics(self):
        """Print formatted statistics to console"""
        insights = self.analyze_bark_patterns()

        print("\n" + "="*60)
        print("BARK DETECTION STATISTICS")
        print("="*60)
        print(f"\nTotal Events (5-min grouping): {insights['total_events']}")
        print(f"Average Event Duration: {insights['avg_duration_5min']:.1f} minutes")

        if insights['longest_event']:
            print(f"\nLongest Event:")
            print(f"  Date: {insights['longest_event']['date']}")
            print(f"  Time: {insights['longest_event']['start_time']}")
            print(f"  Duration: {insights['longest_event']['duration']:.1f} minutes")

        if insights['peak_hours']:
            print(f"\nPeak Barking Hours:")
            for hour in insights['peak_hours']:
                print(f"  - {hour}")

        if insights['quietest_hours']:
            print(f"\nQuietest Hours:")
            for hour in insights['quietest_hours']:
                print(f"  - {hour}")

        print("\n" + "="*60 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Export dog bark and bird detection data to CSV')
    parser.add_argument('--all', action='store_true', help='Export all CSV files')
    parser.add_argument('--5min', action='store_true', help='Export 5-minute bark events')
    parser.add_argument('--10min', action='store_true', help='Export 10-minute bark events')
    parser.add_argument('--birds', action='store_true', help='Export bird detections')
    parser.add_argument('--daily', action='store_true', help='Generate daily summary')
    parser.add_argument('--weekly', action='store_true', help='Generate weekly report')
    parser.add_argument('--stats', action='store_true', help='Print statistics')

    args = parser.parse_args()

    exporter = CSVExporter()
    analyzer = StatisticsAnalyzer()

    # If no specific action, export all
    if not any([args.all, args.five_min, args.ten_min, args.birds, args.daily, args.weekly, args.stats]):
        args.all = True

    if args.all:
        exporter.export_all()

    if args.five_min or args.all:
        exporter.export_bark_events_5min()

    if args.ten_min or args.all:
        exporter.export_bark_events_10min()

    if args.birds or args.all:
        exporter.export_bird_detections()

    if args.daily or args.all:
        exporter.generate_daily_summary()

    if args.weekly or args.all:
        exporter.generate_weekly_report()

    if args.stats:
        analyzer.print_statistics()

if __name__ == "__main__":
    main()
