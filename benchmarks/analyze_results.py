import json
import glob
import os
import pandas as pd
import sys

def analyze_latest():
    # Find latest JSON result
    list_of_files = glob.glob('benchmarks/results/*.json') 
    if not list_of_files:
        print("No benchmark results found.")
        return
        
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Analyzing {latest_file}...")
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
        
    df = pd.DataFrame(data)
    
    # Filter out errors
    if "error" in df.columns:
        # Handle both None/NaN and empty strings
        df = df[df["error"].isna() | (df["error"] == "")]

    if df.empty:
        print("No successful results to analyze.")
        return
        
    # Overall Metrics
    total_prompts = len(df)
    avg_latency = df["total_latency"].mean()
    avg_speedup = df["speedup"].mean()
    overall_success = df["success_rate"].mean()
    mode_accuracy = df["mode_accuracy"].mean() * 100
    
    # Category Analysis
    category_stats = df.groupby("category").agg({
        "total_latency": "mean",
        "speedup": "mean",
        "success_rate": "mean",
        "mode_accuracy": "mean"
    }).round(2)
    
    # Generate Markdown Report
    report = f"""# 📊 ParaMind Benchmark Report
**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
**Source:** `{latest_file}`

## 🚀 Executive Summary
| Metric | Value |
|--------|-------|
| **Total Prompts** | {total_prompts} |
| **Avg Latency** | {avg_latency:.2f}s |
| **Avg Speedup** | {avg_speedup:.2f}x |
| **Success Rate** | {overall_success:.1f}% |
| **Mode Accuracy** | {mode_accuracy:.1f}% |

## 📂 Category Performance
{category_stats.to_markdown()}

## 🔍 Detailed Insights
- **Fastest Prompt:** {df.loc[df['total_latency'].idxmin()]['prompt'][:50]}... ({df['total_latency'].min():.2f}s)
- **Slowest Prompt:** {df.loc[df['total_latency'].idxmax()]['prompt'][:50]}... ({df['total_latency'].max():.2f}s)
- **Best Speedup:** {df.loc[df['speedup'].idxmax()]['prompt'][:50]}... ({df['speedup'].max():.2f}x)

## 📋 Failed/Error Prompts
"""
    # Add failures if any
    failures = df[df["success_rate"] < 100]
    if not failures.empty:
        report += failures[["prompt_id", "prompt", "success_rate"]].to_markdown()
    else:
        report += "None! 🎉"

    # Save Report
    report_path = latest_file.replace(".json", "_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"Report generated: {report_path}")

if __name__ == "__main__":
    analyze_latest()
