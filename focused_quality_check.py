#!/usr/bin/env python3
"""
Focused Code Quality Check for Integrated MRUpdater Files

This script performs a focused quality check on the key integrated files
that were enhanced during the codebase integration process.
"""

import ast
import os
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class FocusedQualityChecker:
    """Focused quality checker for integrated files."""
    
    def __init__(self):
        """Initialize the focused quality checker."""
        # Key files that were integrated/enhanced
        self.key_files = [
            'main.py',
            'cartclinic/gui.py',
            'cartclinic/cartridge_read.py',
            'cartclinic/cartridge_write.py',
            'cartclinic/exceptions.py',
            'flashing_tool/chromatic.py',
            'flashing_tool/gui.py',
            'flashing_tool/util.py',
            'flashing_tool/esp_util.py',
            'config.py',
            'error_handler.py',
            'compatibility_layer.py',
            'api_versioning.py',
            'data_format_migration.py',
            'libpyretro/util.py',
            'libpyretro/ips_util.py'
        ]
        
        self.results = {}
        self.issues = []
        self.recommendations = []
    
    def check_all_files(self) -> Dict[str, Any]:
        """
        Check all key integrated files for quality issues.
        
        Returns:
            Dictionary with quality check results
        """
        logger.info("Starting focused quality check on integrated files")
        
        total_files = 0
        valid_files = 0
        total_issues = 0
        
        for file_path in self.key_files:
            if not os.path.exists(file_path):
                self.issues.append(f"Missing key file: {file_path}")
                continue
            
            total_files += 1
            file_results = self._check_file(file_path)
            
            if file_results['valid']:
                valid_files += 1
            
            total_issues += len(file_results['issues'])
            self.results[file_path] = file_results
        
        # Generate overall assessment
        overall_results = {
            'total_files': total_files,
            'valid_files': valid_files,
            'total_issues': total_issues,
            'file_results': self.results,
            'overall_issues': self.issues,
            'recommendations': self._generate_recommendations()
        }
        
        logger.info(f"Quality check completed: {valid_files}/{total_files} files valid")
        return overall_results
    
    def _check_file(self, file_path: str) -> Dict[str, Any]:
        """
        Check a single file for quality issues.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            Dictionary with file check results
        """
        results = {
            'valid': False,
            'issues': [],
            'metrics': {},
            'recommendations': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Parse AST
            try:
                tree = ast.parse(content)
                results['valid'] = True
            except SyntaxError as e:
                results['issues'].append(f"Syntax error: {e}")
                return results
            
            # Check various quality aspects
            results['metrics'] = self._analyze_file_metrics(tree, content, lines)
            results['issues'].extend(self._check_documentation(tree, file_path))
            results['issues'].extend(self._check_complexity(tree, file_path))
            results['issues'].extend(self._check_error_handling(tree, file_path))
            results['issues'].extend(self._check_code_style(lines, file_path))
            results['issues'].extend(self._check_integration_quality(content, file_path))
            
        except Exception as e:
            results['issues'].append(f"Failed to analyze file: {e}")
        
        return results
    
    def _analyze_file_metrics(self, tree: ast.AST, content: str, lines: List[str]) -> Dict[str, Any]:
        """Analyze basic file metrics."""
        metrics = {
            'lines_of_code': len(lines),
            'functions': 0,
            'classes': 0,
            'documented_functions': 0,
            'documented_classes': 0,
            'complex_functions': 0,
            'functions_with_error_handling': 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics['functions'] += 1
                
                # Check documentation
                if ast.get_docstring(node):
                    metrics['documented_functions'] += 1
                
                # Check complexity (simplified)
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    func_length = node.end_lineno - node.lineno
                    if func_length > 50:
                        metrics['complex_functions'] += 1
                
                # Check error handling
                for child in ast.walk(node):
                    if isinstance(child, ast.Try):
                        metrics['functions_with_error_handling'] += 1
                        break
            
            elif isinstance(node, ast.ClassDef):
                metrics['classes'] += 1
                if ast.get_docstring(node):
                    metrics['documented_classes'] += 1
        
        return metrics
    
    def _check_documentation(self, tree: ast.AST, file_path: str) -> List[str]:
        """Check documentation quality."""
        issues = []
        
        # Check module docstring
        if not ast.get_docstring(tree):
            issues.append(f"Missing module docstring in {file_path}")
        
        # Check function and class docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_') and not ast.get_docstring(node):
                    # Only flag public functions without docstrings
                    if hasattr(node, 'end_lineno') and node.end_lineno:
                        func_length = node.end_lineno - node.lineno
                        if func_length > 5:  # Only flag non-trivial functions
                            issues.append(f"Missing docstring for function {node.name} in {file_path}")
            
            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    issues.append(f"Missing docstring for class {node.name} in {file_path}")
        
        return issues
    
    def _check_complexity(self, tree: ast.AST, file_path: str) -> List[str]:
        """Check code complexity."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    func_length = node.end_lineno - node.lineno
                    if func_length > 100:
                        issues.append(f"Very long function {node.name} in {file_path} ({func_length} lines)")
                    elif func_length > 50:
                        issues.append(f"Long function {node.name} in {file_path} ({func_length} lines)")
        
        return issues
    
    def _check_error_handling(self, tree: ast.AST, file_path: str) -> List[str]:
        """Check error handling coverage."""
        issues = []
        
        # Functions that should have error handling
        risky_function_patterns = [
            'read', 'write', 'open', 'connect', 'load', 'save', 'parse',
            'flash', 'device', 'usb', 'serial', 'network', 'file'
        ]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function name suggests it might need error handling
                needs_error_handling = any(
                    pattern in node.name.lower() 
                    for pattern in risky_function_patterns
                )
                
                if needs_error_handling:
                    # Check if function has try-except blocks
                    has_error_handling = any(
                        isinstance(child, ast.Try) 
                        for child in ast.walk(node)
                    )
                    
                    if not has_error_handling:
                        issues.append(f"Function {node.name} in {file_path} may need error handling")
        
        return issues
    
    def _check_code_style(self, lines: List[str], file_path: str) -> List[str]:
        """Check code style issues."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 120:  # More lenient than 100 for integrated code
                issues.append(f"Long line ({len(line)} chars) in {file_path}:{i}")
            
            # Check for debugging code
            if any(debug in line.lower() for debug in ['print(', 'console.log', 'debugger']):
                # Allow logging statements
                if 'logger.' not in line and 'logging.' not in line:
                    issues.append(f"Potential debug code in {file_path}:{i}")
        
        return issues
    
    def _check_integration_quality(self, content: str, file_path: str) -> List[str]:
        """Check integration-specific quality aspects."""
        issues = []
        
        # Check for backward compatibility considerations
        if file_path in ['main.py', 'cartclinic/gui.py', 'flashing_tool/chromatic.py']:
            if 'compatibility' not in content.lower() and 'backward' not in content.lower():
                issues.append(f"No backward compatibility considerations in {file_path}")
        
        # Check for enhanced error handling in key files
        if file_path in ['error_handler.py', 'compatibility_layer.py']:
            if 'try:' not in content or 'except' not in content:
                issues.append(f"Insufficient error handling in {file_path}")
        
        # Check for proper imports in compatibility layer
        if file_path == 'compatibility_layer.py':
            required_imports = ['typing', 'logging', 'warnings']
            for imp in required_imports:
                if f'import {imp}' not in content and f'from {imp}' not in content:
                    issues.append(f"Missing {imp} import in {file_path}")
        
        return issues
    
    def _generate_recommendations(self) -> List[str]:
        """Generate specific recommendations based on findings."""
        recommendations = []
        
        # Count issues by type
        doc_issues = sum(1 for issue in self.issues if 'docstring' in issue)
        complexity_issues = sum(1 for issue in self.issues if 'long function' in issue.lower())
        error_handling_issues = sum(1 for issue in self.issues if 'error handling' in issue)
        style_issues = sum(1 for issue in self.issues if 'long line' in issue or 'debug code' in issue)
        
        if doc_issues > 0:
            recommendations.append(
                f"Add docstrings to {doc_issues} functions/classes. "
                "Focus on public APIs and complex functions."
            )
        
        if complexity_issues > 0:
            recommendations.append(
                f"Refactor {complexity_issues} complex functions. "
                "Break them into smaller, single-purpose functions."
            )
        
        if error_handling_issues > 0:
            recommendations.append(
                f"Add error handling to {error_handling_issues} functions. "
                "Focus on I/O operations and external interactions."
            )
        
        if style_issues > 0:
            recommendations.append(
                f"Fix {style_issues} style issues. "
                "Keep lines under 120 characters and remove debug code."
            )
        
        return recommendations
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a focused quality report."""
        report = []
        report.append("=" * 60)
        report.append("MRUpdater Focused Code Quality Report")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        report.append("SUMMARY")
        report.append("-" * 7)
        report.append(f"Files analyzed: {results['total_files']}")
        report.append(f"Valid files: {results['valid_files']}")
        report.append(f"Total issues: {results['total_issues']}")
        report.append("")
        
        # File-by-file results
        report.append("FILE ANALYSIS")
        report.append("-" * 13)
        
        for file_path, file_results in results['file_results'].items():
            status = "✅ PASS" if len(file_results['issues']) == 0 else f"⚠️  {len(file_results['issues'])} issues"
            report.append(f"{file_path}: {status}")
            
            if file_results['issues']:
                for issue in file_results['issues'][:3]:  # Show first 3 issues per file
                    report.append(f"  • {issue}")
                if len(file_results['issues']) > 3:
                    report.append(f"  • ... and {len(file_results['issues']) - 3} more issues")
        
        report.append("")
        
        # Key metrics
        report.append("KEY METRICS")
        report.append("-" * 11)
        
        total_functions = sum(fr['metrics'].get('functions', 0) for fr in results['file_results'].values())
        total_classes = sum(fr['metrics'].get('classes', 0) for fr in results['file_results'].values())
        documented_functions = sum(fr['metrics'].get('documented_functions', 0) for fr in results['file_results'].values())
        documented_classes = sum(fr['metrics'].get('documented_classes', 0) for fr in results['file_results'].values())
        
        if total_functions > 0:
            doc_coverage = ((documented_functions + documented_classes) / (total_functions + total_classes)) * 100
            report.append(f"Documentation coverage: {doc_coverage:.1f}%")
        
        report.append(f"Total functions: {total_functions}")
        report.append(f"Total classes: {total_classes}")
        report.append("")
        
        # Recommendations
        if results['recommendations']:
            report.append("RECOMMENDATIONS")
            report.append("-" * 15)
            for i, rec in enumerate(results['recommendations'], 1):
                report.append(f"{i}. {rec}")
            report.append("")
        
        # Overall assessment
        report.append("OVERALL ASSESSMENT")
        report.append("-" * 18)
        
        if results['total_issues'] == 0:
            report.append("✅ Excellent - No issues detected")
        elif results['total_issues'] <= 10:
            report.append("✅ Good - Minor issues that can be easily addressed")
        elif results['total_issues'] <= 30:
            report.append("⚠️  Fair - Some issues need attention")
        else:
            report.append("❌ Needs Improvement - Significant issues detected")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """Main function to run focused quality check."""
    checker = FocusedQualityChecker()
    results = checker.check_all_files()
    
    # Generate and save report
    report = checker.generate_report(results)
    
    with open('focused_quality_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Print summary
    print(report)
    
    # Return appropriate exit code
    if results['total_issues'] <= 10:
        return 0
    elif results['total_issues'] <= 30:
        return 1
    else:
        return 2


if __name__ == "__main__":
    exit(main())