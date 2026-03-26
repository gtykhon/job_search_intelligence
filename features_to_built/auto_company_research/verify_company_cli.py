#!/usr/bin/env python3
"""
Company Verification CLI
Command-line interface for company screening and research

Usage:
    python verify_company_cli.py "Netflix" "Analytics Engineer"
    python verify_company_cli.py --batch companies.txt
    python verify_company_cli.py --interactive
"""

import sys
import argparse
import json
from pathlib import Path
from company_verification_system import (
    CompanyVerificationSystem,
    DecisionStatus
)


def verify_single_company(system: CompanyVerificationSystem, 
                         company_name: str, 
                         position: str = "",
                         output_format: str = "text") -> None:
    """Verify a single company and print results"""
    
    result = system.verify_company(company_name, position)
    
    if output_format == "json":
        # Output as JSON
        output = {
            "company": result.company_name,
            "position": result.position,
            "decision": result.decision_status.value,
            "defense_status": result.defense_status.value if result.defense_status else None,
            "decline_reason": result.decline_reason,
            "time_saved_minutes": result.time_saved_minutes,
            "research_date": result.research_date
        }
        
        if result.glassdoor_metrics:
            output["glassdoor"] = {
                "overall_rating": result.glassdoor_metrics.overall_rating,
                "culture_values": result.glassdoor_metrics.culture_values,
                "work_life_balance": result.glassdoor_metrics.work_life_balance,
                "ceo_approval": result.glassdoor_metrics.ceo_approval,
                "total_reviews": result.glassdoor_metrics.total_reviews
            }
            
        if result.scoring_result:
            output["scores"] = {
                "culture_score": result.scoring_result.culture_score,
                "culture_rating": result.scoring_result.culture_rating,
                "wlb_score": result.scoring_result.wlb_score,
                "wlb_rating": result.scoring_result.wlb_rating,
                "risk_level": result.scoring_result.risk_level
            }
            
        print(json.dumps(output, indent=2))
        
    else:
        # Output as text report
        report = system.generate_report(result)
        print(report)
        
    # Return exit code based on decision
    if result.decision_status == DecisionStatus.AUTO_DECLINE:
        return 2  # Auto-declined
    elif result.decision_status == DecisionStatus.USER_DECISION:
        return 1  # Needs user decision
    else:
        return 0  # Proceed


def verify_batch(system: CompanyVerificationSystem,
                batch_file: str,
                output_dir: str = "./reports/") -> None:
    """Verify multiple companies from a file"""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Read batch file (format: company_name, position)
    companies = []
    with open(batch_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(',', 1)
            company = parts[0].strip()
            position = parts[1].strip() if len(parts) > 1 else ""
            companies.append((company, position))
    
    print(f"\nBatch Processing: {len(companies)} companies\n")
    print("="*70)
    
    results = []
    for i, (company, position) in enumerate(companies, 1):
        print(f"\n[{i}/{len(companies)}] Verifying: {company}")
        print("-"*70)
        
        result = system.verify_company(company, position)
        results.append(result)
        
        # Save individual report
        filename = company.replace(' ', '_').replace('/', '_') + '.txt'
        report_path = output_path / filename
        with open(report_path, 'w') as f:
            f.write(system.generate_report(result))
        
        print(f"Decision: {result.decision_status.value}")
        if result.time_saved_minutes > 0:
            print(f"Time saved: {result.time_saved_minutes} minutes")
    
    # Generate summary
    print("\n" + "="*70)
    print("BATCH SUMMARY")
    print("="*70)
    
    auto_declined = sum(1 for r in results if r.decision_status == DecisionStatus.AUTO_DECLINE)
    proceed = sum(1 for r in results if r.decision_status == DecisionStatus.PROCEED)
    user_decision = sum(1 for r in results if r.decision_status == DecisionStatus.USER_DECISION)
    database_hits = sum(1 for r in results if r.decision_status == DecisionStatus.DATABASE_HIT)
    total_time_saved = sum(r.time_saved_minutes for r in results)
    
    print(f"\nCompanies Screened: {len(results)}")
    print(f"  Auto-Declined: {auto_declined}")
    print(f"  Proceed: {proceed}")
    print(f"  User Decision Required: {user_decision}")
    print(f"  Database Hits: {database_hits}")
    print(f"\nTotal Time Saved: {total_time_saved} minutes (~{total_time_saved/60:.1f} hours)")
    print(f"Reports saved to: {output_path.absolute()}")
    
    # Save summary as JSON
    summary_path = output_path / "batch_summary.json"
    summary = {
        "total_companies": len(results),
        "auto_declined": auto_declined,
        "proceed": proceed,
        "user_decision": user_decision,
        "database_hits": database_hits,
        "total_time_saved_minutes": total_time_saved,
        "companies": [
            {
                "company": r.company_name,
                "position": r.position,
                "decision": r.decision_status.value,
                "time_saved": r.time_saved_minutes
            }
            for r in results
        ]
    }
    
    with open(summary_path, 'w') as f:
        json.dumps(summary, indent=2)
    
    print(f"Summary saved to: {summary_path}")


def interactive_mode(system: CompanyVerificationSystem) -> None:
    """Interactive mode for verifying companies"""
    
    print("\n" + "="*70)
    print("COMPANY VERIFICATION - INTERACTIVE MODE")
    print("="*70)
    print("\nEnter company information (or 'quit' to exit)\n")
    
    while True:
        try:
            company = input("Company name: ").strip()
            
            if company.lower() in ['quit', 'exit', 'q']:
                print("\nExiting interactive mode.")
                break
                
            if not company:
                print("Please enter a company name.")
                continue
                
            position = input("Position (optional): ").strip()
            
            print("\n" + "-"*70)
            result = system.verify_company(company, position)
            print("-"*70)
            
            # Show quick summary
            print(f"\nDecision: {result.decision_status.value}")
            
            if result.decline_reason:
                print(f"Reason: {result.decline_reason}")
                
            if result.scoring_result:
                print(f"Culture: {result.scoring_result.culture_score}/100 ({result.scoring_result.culture_rating})")
                print(f"WLB: {result.scoring_result.wlb_score}/100 ({result.scoring_result.wlb_rating})")
                print(f"Risk: {result.scoring_result.risk_level}")
            
            # Ask if user wants full report
            show_full = input("\nShow full report? (y/n): ").strip().lower()
            if show_full == 'y':
                print("\n" + system.generate_report(result))
            
            # Ask if user wants to save report
            save_report = input("\nSave report to file? (y/n): ").strip().lower()
            if save_report == 'y':
                filename = f"{company.replace(' ', '_')}_report.txt"
                with open(filename, 'w') as f:
                    f.write(system.generate_report(result))
                print(f"Report saved to: {filename}")
            
            print("\n" + "="*70)
            
        except KeyboardInterrupt:
            print("\n\nExiting interactive mode.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.\n")


def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description='Company Verification System - Automated company screening and research',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify single company
  %(prog)s "Netflix" "Analytics Engineer 5"
  
  # Batch processing from file
  %(prog)s --batch companies.txt --output ./reports/
  
  # Interactive mode
  %(prog)s --interactive
  
  # JSON output
  %(prog)s "Docker" "Staff Engineer" --format json
  
Batch file format (companies.txt):
  Netflix, Analytics Engineer 5
  Watershed, Senior Data Engineer
  Docker, Staff Platform Engineer
  # Comments start with #
        """
    )
    
    # Positional arguments
    parser.add_argument('company', nargs='?', help='Company name')
    parser.add_argument('position', nargs='?', default='', help='Position title')
    
    # Optional arguments
    parser.add_argument('--batch', '-b', metavar='FILE',
                       help='Batch process companies from file')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--output', '-o', default='./reports/',
                       help='Output directory for reports (default: ./reports/)')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--database', '-d', default='/mnt/project/company_research_database.md',
                       help='Path to company database file')
    
    args = parser.parse_args()
    
    # Initialize system
    system = CompanyVerificationSystem(database_path=args.database)
    
    # Determine mode
    if args.interactive:
        interactive_mode(system)
    elif args.batch:
        verify_batch(system, args.batch, args.output)
    elif args.company:
        exit_code = verify_single_company(system, args.company, args.position, args.format)
        sys.exit(exit_code)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
