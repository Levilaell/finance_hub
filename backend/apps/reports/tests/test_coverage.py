"""
Test coverage validation and reporting for reports app
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple


class TestCoverageValidator:
    """Validates test coverage for the reports app"""
    
    def __init__(self, app_path: str = 'apps.reports'):
        self.app_path = app_path
        self.coverage_thresholds = {
            'total': 90,  # Overall coverage should be at least 90%
            'models': 95,  # Models should have 95% coverage
            'views': 85,   # Views should have 85% coverage
            'services': 90, # Services should have 90% coverage
            'tasks': 85,   # Tasks should have 85% coverage
            'utils': 90,   # Utilities should have 90% coverage
        }
        
        self.required_test_files = [
            'test_models.py',
            'test_serializers.py', 
            'test_api_views.py',
            'test_services.py',
            'test_tasks.py',
            'test_integration.py',
            'factories.py'
        ]
        
        self.test_categories = {
            'unit': [
                'test_models.py',
                'test_serializers.py',
                'test_services.py'
            ],
            'integration': [
                'test_api_views.py',
                'test_tasks.py'
            ],
            'e2e': [
                'test_integration.py'
            ]
        }
    
    def validate_test_structure(self) -> Dict[str, bool]:
        """Validate that all required test files exist"""
        tests_dir = Path(__file__).parent
        results = {}
        
        for test_file in self.required_test_files:
            file_path = tests_dir / test_file
            results[test_file] = file_path.exists()
        
        return results
    
    def run_tests_with_coverage(self) -> Tuple[bool, Dict]:
        """Run tests with coverage reporting"""
        try:
            # Run coverage with Django tests
            cmd = [
                'coverage', 'run',
                '--source', self.app_path,
                '--omit', '*/migrations/*,*/tests/*,*/venv/*,*/env/*',
                'manage.py', 'test', self.app_path,
                '--verbosity=2'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent
            )
            
            if result.returncode != 0:
                print(f"Tests failed: {result.stderr}")
                return False, {}
            
            # Generate coverage report
            coverage_cmd = ['coverage', 'report', '--format=json']
            coverage_result = subprocess.run(
                coverage_cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent
            )
            
            if coverage_result.returncode == 0:
                coverage_data = json.loads(coverage_result.stdout)
                return True, coverage_data
            else:
                print(f"Coverage report failed: {coverage_result.stderr}")
                return False, {}
                
        except Exception as e:
            print(f"Error running tests with coverage: {e}")
            return False, {}
    
    def analyze_coverage(self, coverage_data: Dict) -> Dict:
        """Analyze coverage data against thresholds"""
        analysis = {
            'overall': {
                'coverage': coverage_data.get('totals', {}).get('percent_covered', 0),
                'threshold': self.coverage_thresholds['total'],
                'passed': False,
                'lines_covered': coverage_data.get('totals', {}).get('covered_lines', 0),
                'lines_total': coverage_data.get('totals', {}).get('num_statements', 0)
            },
            'files': {},
            'missing_coverage': []
        }
        
        # Check overall coverage
        overall_coverage = analysis['overall']['coverage']
        analysis['overall']['passed'] = overall_coverage >= self.coverage_thresholds['total']
        
        # Analyze file-level coverage
        files = coverage_data.get('files', {})
        
        for file_path, file_data in files.items():
            if self.app_path.replace('.', '/') in file_path:
                # Determine file category
                category = self._categorize_file(file_path)
                threshold = self.coverage_thresholds.get(category, self.coverage_thresholds['total'])
                
                file_coverage = file_data.get('summary', {}).get('percent_covered', 0)
                
                analysis['files'][file_path] = {
                    'coverage': file_coverage,
                    'threshold': threshold,
                    'passed': file_coverage >= threshold,
                    'category': category,
                    'lines_covered': file_data.get('summary', {}).get('covered_lines', 0),
                    'lines_total': file_data.get('summary', {}).get('num_statements', 0),
                    'missing_lines': file_data.get('missing_lines', [])
                }
                
                # Track files with insufficient coverage
                if file_coverage < threshold:
                    analysis['missing_coverage'].append({
                        'file': file_path,
                        'coverage': file_coverage,
                        'threshold': threshold,
                        'missing_lines': file_data.get('missing_lines', [])
                    })
        
        return analysis
    
    def _categorize_file(self, file_path: str) -> str:
        """Categorize a file based on its path"""
        if 'models.py' in file_path:
            return 'models'
        elif 'views.py' in file_path or 'api' in file_path:
            return 'views'
        elif 'services' in file_path:
            return 'services'
        elif 'tasks.py' in file_path:
            return 'tasks'
        elif 'utils' in file_path or 'helpers' in file_path:
            return 'utils'
        else:
            return 'other'
    
    def generate_report(self, analysis: Dict) -> str:
        """Generate a comprehensive coverage report"""
        report_lines = [
            "=" * 80,
            "REPORTS APP TEST COVERAGE REPORT",
            "=" * 80,
            "",
            "OVERALL COVERAGE:",
            f"  Total Coverage: {analysis['overall']['coverage']:.1f}%",
            f"  Threshold: {analysis['overall']['threshold']}%",
            f"  Status: {'✅ PASSED' if analysis['overall']['passed'] else '❌ FAILED'}",
            f"  Lines Covered: {analysis['overall']['lines_covered']}/{analysis['overall']['lines_total']}",
            "",
            "FILE-LEVEL COVERAGE:",
            "-" * 40
        ]
        
        # Sort files by coverage percentage
        sorted_files = sorted(
            analysis['files'].items(),
            key=lambda x: x[1]['coverage'],
            reverse=True
        )
        
        for file_path, file_data in sorted_files:
            status_icon = "✅" if file_data['passed'] else "❌"
            report_lines.append(
                f"  {status_icon} {file_path.split('/')[-1]}: "
                f"{file_data['coverage']:.1f}% "
                f"(threshold: {file_data['threshold']}%)"
            )
        
        if analysis['missing_coverage']:
            report_lines.extend([
                "",
                "FILES NEEDING ATTENTION:",
                "-" * 40
            ])
            
            for item in analysis['missing_coverage']:
                report_lines.extend([
                    f"  📝 {item['file'].split('/')[-1]}:",
                    f"     Coverage: {item['coverage']:.1f}% (need {item['threshold']}%)",
                    f"     Missing lines: {item['missing_lines'][:10]}{'...' if len(item['missing_lines']) > 10 else ''}",
                    ""
                ])
        
        # Test structure validation
        test_structure = self.validate_test_structure()
        report_lines.extend([
            "TEST STRUCTURE:",
            "-" * 40
        ])
        
        for test_file, exists in test_structure.items():
            status_icon = "✅" if exists else "❌"
            report_lines.append(f"  {status_icon} {test_file}")
        
        # Test categories summary
        report_lines.extend([
            "",
            "TEST CATEGORIES:",
            "-" * 40
        ])
        
        for category, files in self.test_categories.items():
            existing_files = [f for f in files if test_structure.get(f, False)]
            total_files = len(files)
            existing_count = len(existing_files)
            
            status_icon = "✅" if existing_count == total_files else "⚠️" if existing_count > 0 else "❌"
            report_lines.append(f"  {status_icon} {category.upper()}: {existing_count}/{total_files} files")
        
        report_lines.extend([
            "",
            "RECOMMENDATIONS:",
            "-" * 40
        ])
        
        recommendations = self._generate_recommendations(analysis, test_structure)
        for rec in recommendations:
            report_lines.append(f"  • {rec}")
        
        report_lines.extend([
            "",
            "=" * 80,
            f"SUMMARY: {'✅ ALL CHECKS PASSED' if self._all_checks_passed(analysis, test_structure) else '❌ SOME CHECKS FAILED'}",
            "=" * 80
        ])
        
        return "\n".join(report_lines)
    
    def _generate_recommendations(self, analysis: Dict, test_structure: Dict) -> List[str]:
        """Generate recommendations based on coverage analysis"""
        recommendations = []
        
        # Coverage recommendations
        if not analysis['overall']['passed']:
            recommendations.append(
                f"Increase overall test coverage from {analysis['overall']['coverage']:.1f}% to at least {analysis['overall']['threshold']}%"
            )
        
        # File-specific recommendations
        for item in analysis['missing_coverage'][:3]:  # Top 3 files needing attention
            recommendations.append(
                f"Add tests for {item['file'].split('/')[-1]} (currently {item['coverage']:.1f}%, need {item['threshold']}%)"
            )
        
        # Missing test files
        missing_files = [f for f, exists in test_structure.items() if not exists]
        if missing_files:
            recommendations.append(f"Create missing test files: {', '.join(missing_files)}")
        
        # Test category recommendations
        for category, files in self.test_categories.items():
            existing_files = [f for f in files if test_structure.get(f, False)]
            if len(existing_files) < len(files):
                missing = [f for f in files if not test_structure.get(f, False)]
                recommendations.append(f"Complete {category} test coverage by adding: {', '.join(missing)}")
        
        if not recommendations:
            recommendations.append("All coverage thresholds met! Consider adding edge case tests and performance tests.")
        
        return recommendations
    
    def _all_checks_passed(self, analysis: Dict, test_structure: Dict) -> bool:
        """Check if all validation criteria are met"""
        # Overall coverage check
        if not analysis['overall']['passed']:
            return False
        
        # File coverage checks
        for file_data in analysis['files'].values():
            if not file_data['passed']:
                return False
        
        # Test structure checks
        if not all(test_structure.values()):
            return False
        
        return True
    
    def save_html_report(self) -> str:
        """Generate and save HTML coverage report"""
        try:
            cmd = ['coverage', 'html', '--directory=htmlcov']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent
            )
            
            if result.returncode == 0:
                html_path = Path(__file__).parent.parent.parent.parent / 'htmlcov' / 'index.html'
                return str(html_path)
            else:
                print(f"HTML report generation failed: {result.stderr}")
                return ""
                
        except Exception as e:
            print(f"Error generating HTML report: {e}")
            return ""
    
    def run_full_validation(self) -> bool:
        """Run complete test coverage validation"""
        print("🚀 Starting Reports App Test Coverage Validation...")
        print()
        
        # Step 1: Validate test structure
        print("📁 Validating test structure...")
        test_structure = self.validate_test_structure()
        missing_files = [f for f, exists in test_structure.items() if not exists]
        
        if missing_files:
            print(f"❌ Missing test files: {', '.join(missing_files)}")
        else:
            print("✅ All required test files present")
        
        print()
        
        # Step 2: Run tests with coverage
        print("🧪 Running tests with coverage analysis...")
        tests_passed, coverage_data = self.run_tests_with_coverage()
        
        if not tests_passed:
            print("❌ Tests failed - cannot proceed with coverage analysis")
            return False
        
        print("✅ All tests passed")
        print()
        
        # Step 3: Analyze coverage
        print("📊 Analyzing coverage data...")
        analysis = self.analyze_coverage(coverage_data)
        
        # Step 4: Generate reports
        print("📄 Generating coverage report...")
        text_report = self.generate_report(analysis)
        print(text_report)
        
        # Save text report
        report_path = Path(__file__).parent / 'coverage_report.txt'
        with open(report_path, 'w') as f:
            f.write(text_report)
        print(f"💾 Text report saved to: {report_path}")
        
        # Generate HTML report
        html_path = self.save_html_report()
        if html_path:
            print(f"🌐 HTML report saved to: {html_path}")
        
        # Step 5: Return overall status
        all_passed = self._all_checks_passed(analysis, test_structure)
        
        if all_passed:
            print("\n🎉 All coverage validation checks passed!")
        else:
            print("\n⚠️  Some coverage validation checks failed. See recommendations above.")
        
        return all_passed


def main():
    """Main entry point for coverage validation"""
    validator = TestCoverageValidator()
    success = validator.run_full_validation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()