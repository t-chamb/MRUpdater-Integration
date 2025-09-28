#!/usr/bin/env python3
"""
Code Quality Validator for MRUpdater Integration

This script validates code quality and maintainability across the integrated
MRUpdater codebase. It checks for:
- Code style and formatting consistency
- Documentation completeness
- Error handling coverage
- Code complexity metrics
- Maintainability indicators
- Integration quality
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class CodeQualityMetrics:
    """Data class for code quality metrics."""
    
    # File-level metrics
    total_files: int = 0
    total_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    
    # Documentation metrics
    documented_functions: int = 0
    documented_classes: int = 0
    documentation_coverage: float = 0.0
    
    # Complexity metrics
    average_function_length: float = 0.0
    max_function_length: int = 0
    complex_functions: int = 0
    
    # Error handling metrics
    functions_with_error_handling: int = 0
    error_handling_coverage: float = 0.0
    
    # Code style metrics
    style_violations: int = 0
    naming_violations: int = 0
    
    # Maintainability metrics
    maintainability_score: float = 0.0
    technical_debt_indicators: int = 0
    
    # Integration quality metrics
    integration_issues: int = 0
    compatibility_issues: int = 0


class CodeQualityValidator:
    """Validates code quality and maintainability."""
    
    def __init__(self, root_path: str = "."):
        """
        Initialize code quality validator.
        
        Args:
            root_path: Root path to analyze
        """
        self.root_path = Path(root_path)
        self.metrics = CodeQualityMetrics()
        self.issues = []
        self.recommendations = []
        
        # Patterns for various checks
        self.todo_pattern = re.compile(r'#\s*TODO|#\s*FIXME|#\s*HACK', re.IGNORECASE)
        self.debug_pattern = re.compile(r'print\s*\(|console\.log|debugger', re.IGNORECASE)
        self.placeholder_pattern = re.compile(r'placeholder|temporary|temp|stub', re.IGNORECASE)
        
        # Files to analyze
        self.python_files = []
        self._find_python_files()
    
    def _find_python_files(self):
        """Find all Python files to analyze."""
        exclude_patterns = [
            '__pycache__',
            '.git',
            '.vscode',
            'venv',
            'env',
            '.pytest_cache',
            'build',
            'dist'
        ]
        
        for file_path in self.root_path.rglob('*.py'):
            # Skip excluded directories
            if any(pattern in str(file_path) for pattern in exclude_patterns):
                continue
            
            self.python_files.append(file_path)
        
        logger.info(f"Found {len(self.python_files)} Python files to analyze")
    
    def validate_all(self) -> CodeQualityMetrics:
        """
        Run all code quality validations.
        
        Returns:
            CodeQualityMetrics with validation results
        """
        logger.info("Starting comprehensive code quality validation")
        
        # Reset metrics
        self.metrics = CodeQualityMetrics()
        self.issues = []
        self.recommendations = []
        
        # Run all validations
        self._validate_file_structure()
        self._validate_documentation()
        self._validate_code_complexity()
        self._validate_error_handling()
        self._validate_code_style()
        self._validate_maintainability()
        self._validate_integration_quality()
        
        # Calculate overall scores
        self._calculate_overall_scores()
        
        logger.info("Code quality validation completed")
        return self.metrics
    
    def _validate_file_structure(self):
        """Validate file structure and organization."""
        logger.info("Validating file structure and organization")
        
        self.metrics.total_files = len(self.python_files)
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.metrics.total_lines += len(content.splitlines())
                
                # Parse AST for structure analysis
                tree = ast.parse(content)
                
                # Count functions and classes
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        self.metrics.total_functions += 1
                    elif isinstance(node, ast.ClassDef):
                        self.metrics.total_classes += 1
                
            except Exception as e:
                self.issues.append(f"Failed to parse {file_path}: {e}")
    
    def _validate_documentation(self):
        """Validate documentation completeness."""
        logger.info("Validating documentation completeness")
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Check module docstring
                if not ast.get_docstring(tree):
                    self.issues.append(f"Missing module docstring: {file_path}")
                
                # Check function and class docstrings
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if ast.get_docstring(node):
                            self.metrics.documented_functions += 1
                        else:
                            # Skip private methods and simple getters/setters
                            if not node.name.startswith('_') and len(node.body) > 1:
                                self.issues.append(
                                    f"Missing docstring for function {node.name} in {file_path}"
                                )
                    
                    elif isinstance(node, ast.ClassDef):
                        if ast.get_docstring(node):
                            self.metrics.documented_classes += 1
                        else:
                            self.issues.append(
                                f"Missing docstring for class {node.name} in {file_path}"
                            )
                
            except Exception as e:
                self.issues.append(f"Documentation validation failed for {file_path}: {e}")
        
        # Calculate documentation coverage
        total_documentable = self.metrics.total_functions + self.metrics.total_classes
        if total_documentable > 0:
            documented_total = self.metrics.documented_functions + self.metrics.documented_classes
            self.metrics.documentation_coverage = (documented_total / total_documentable) * 100
    
    def _validate_code_complexity(self):
        """Validate code complexity metrics."""
        logger.info("Validating code complexity")
        
        function_lengths = []
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                tree = ast.parse(''.join(lines))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Calculate function length
                        start_line = node.lineno
                        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                        function_length = end_line - start_line + 1
                        
                        function_lengths.append(function_length)
                        
                        # Check for overly complex functions
                        if function_length > 50:
                            self.metrics.complex_functions += 1
                            self.issues.append(
                                f"Complex function {node.name} in {file_path} "
                                f"({function_length} lines)"
                            )
                        
                        # Check for deeply nested code
                        max_depth = self._calculate_nesting_depth(node)
                        if max_depth > 4:
                            self.issues.append(
                                f"Deeply nested function {node.name} in {file_path} "
                                f"(depth: {max_depth})"
                            )
                
            except Exception as e:
                self.issues.append(f"Complexity validation failed for {file_path}: {e}")
        
        # Calculate complexity metrics
        if function_lengths:
            self.metrics.average_function_length = sum(function_lengths) / len(function_lengths)
            self.metrics.max_function_length = max(function_lengths)
    
    def _calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth of a node."""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _validate_error_handling(self):
        """Validate error handling coverage."""
        logger.info("Validating error handling coverage")
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        has_error_handling = False
                        
                        # Check for try-except blocks
                        for child in ast.walk(node):
                            if isinstance(child, ast.Try):
                                has_error_handling = True
                                break
                        
                        if has_error_handling:
                            self.metrics.functions_with_error_handling += 1
                        else:
                            # Check if function should have error handling
                            if self._should_have_error_handling(node, content):
                                self.issues.append(
                                    f"Function {node.name} in {file_path} "
                                    f"should have error handling"
                                )
                
            except Exception as e:
                self.issues.append(f"Error handling validation failed for {file_path}: {e}")
        
        # Calculate error handling coverage
        if self.metrics.total_functions > 0:
            self.metrics.error_handling_coverage = (
                self.metrics.functions_with_error_handling / self.metrics.total_functions
            ) * 100
    
    def _should_have_error_handling(self, node: ast.FunctionDef, content: str) -> bool:
        """Determine if a function should have error handling."""
        # Functions that typically need error handling
        risky_patterns = [
            'file', 'open', 'read', 'write', 'connect', 'request',
            'parse', 'load', 'save', 'network', 'device', 'usb'
        ]
        
        function_text = content[node.lineno:node.end_lineno] if hasattr(node, 'end_lineno') else ""
        
        return any(pattern in function_text.lower() for pattern in risky_patterns)
    
    def _validate_code_style(self):
        """Validate code style and naming conventions."""
        logger.info("Validating code style and naming conventions")
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()
                
                tree = ast.parse(content)
                
                # Check line length
                for i, line in enumerate(lines, 1):
                    if len(line) > 100:
                        self.metrics.style_violations += 1
                        self.issues.append(
                            f"Line too long ({len(line)} chars) in {file_path}:{i}"
                        )
                
                # Check naming conventions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not self._is_valid_function_name(node.name):
                            self.metrics.naming_violations += 1
                            self.issues.append(
                                f"Invalid function name '{node.name}' in {file_path}"
                            )
                    
                    elif isinstance(node, ast.ClassDef):
                        if not self._is_valid_class_name(node.name):
                            self.metrics.naming_violations += 1
                            self.issues.append(
                                f"Invalid class name '{node.name}' in {file_path}"
                            )
                
            except Exception as e:
                self.issues.append(f"Style validation failed for {file_path}: {e}")
    
    def _is_valid_function_name(self, name: str) -> bool:
        """Check if function name follows conventions."""
        # Should be snake_case
        return re.match(r'^[a-z_][a-z0-9_]*$', name) is not None
    
    def _is_valid_class_name(self, name: str) -> bool:
        """Check if class name follows conventions."""
        # Should be PascalCase
        return re.match(r'^[A-Z][a-zA-Z0-9]*$', name) is not None
    
    def _validate_maintainability(self):
        """Validate maintainability indicators."""
        logger.info("Validating maintainability indicators")
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for TODO/FIXME comments
                todo_matches = self.todo_pattern.findall(content)
                self.metrics.technical_debt_indicators += len(todo_matches)
                
                # Check for debug code
                debug_matches = self.debug_pattern.findall(content)
                if debug_matches:
                    self.issues.append(
                        f"Debug code found in {file_path}: {len(debug_matches)} instances"
                    )
                
                # Check for placeholder code
                placeholder_matches = self.placeholder_pattern.findall(content)
                if placeholder_matches:
                    self.issues.append(
                        f"Placeholder code found in {file_path}: {len(placeholder_matches)} instances"
                    )
                
                # Check for code duplication (simplified check)
                lines = content.splitlines()
                line_counts = defaultdict(int)
                for line in lines:
                    stripped = line.strip()
                    if len(stripped) > 20 and not stripped.startswith('#'):
                        line_counts[stripped] += 1
                
                duplicated_lines = sum(1 for count in line_counts.values() if count > 1)
                if duplicated_lines > 10:
                    self.issues.append(
                        f"Potential code duplication in {file_path}: "
                        f"{duplicated_lines} duplicated lines"
                    )
                
            except Exception as e:
                self.issues.append(f"Maintainability validation failed for {file_path}: {e}")
    
    def _validate_integration_quality(self):
        """Validate integration-specific quality aspects."""
        logger.info("Validating integration quality")
        
        # Check for integration-specific patterns
        integration_files = [
            'main.py',
            'cartclinic/gui.py',
            'flashing_tool/chromatic.py',
            'config.py',
            'error_handler.py',
            'compatibility_layer.py'
        ]
        
        for file_name in integration_files:
            file_path = self.root_path / file_name
            if not file_path.exists():
                self.metrics.integration_issues += 1
                self.issues.append(f"Missing integration file: {file_name}")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for backward compatibility preservation
                if 'compatibility' not in content.lower() and file_name != 'compatibility_layer.py':
                    self.metrics.compatibility_issues += 1
                    self.issues.append(
                        f"No compatibility considerations found in {file_name}"
                    )
                
                # Check for enhanced error handling
                if 'error' in file_name.lower() or 'exception' in content.lower():
                    if 'try:' not in content or 'except' not in content:
                        self.metrics.integration_issues += 1
                        self.issues.append(
                            f"Insufficient error handling in {file_name}"
                        )
                
            except Exception as e:
                self.issues.append(f"Integration validation failed for {file_name}: {e}")
    
    def _calculate_overall_scores(self):
        """Calculate overall quality scores."""
        # Maintainability score (0-100)
        factors = []
        
        # Documentation factor (0-40 points)
        doc_factor = min(40, self.metrics.documentation_coverage * 0.4)
        factors.append(doc_factor)
        
        # Complexity factor (0-30 points)
        if self.metrics.total_functions > 0:
            complex_ratio = self.metrics.complex_functions / self.metrics.total_functions
            complexity_factor = max(0, 30 - (complex_ratio * 30))
        else:
            complexity_factor = 30
        factors.append(complexity_factor)
        
        # Error handling factor (0-20 points)
        error_factor = min(20, self.metrics.error_handling_coverage * 0.2)
        factors.append(error_factor)
        
        # Style factor (0-10 points)
        if self.metrics.total_lines > 0:
            style_ratio = self.metrics.style_violations / self.metrics.total_lines
            style_factor = max(0, 10 - (style_ratio * 1000))
        else:
            style_factor = 10
        factors.append(style_factor)
        
        self.metrics.maintainability_score = sum(factors)
    
    def generate_report(self) -> str:
        """
        Generate comprehensive code quality report.
        
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("MRUpdater Code Quality Validation Report")
        report.append("=" * 60)
        report.append("")
        
        # Summary metrics
        report.append("SUMMARY METRICS")
        report.append("-" * 20)
        report.append(f"Total files analyzed: {self.metrics.total_files}")
        report.append(f"Total lines of code: {self.metrics.total_lines}")
        report.append(f"Total functions: {self.metrics.total_functions}")
        report.append(f"Total classes: {self.metrics.total_classes}")
        report.append("")
        
        # Documentation metrics
        report.append("DOCUMENTATION QUALITY")
        report.append("-" * 25)
        report.append(f"Documented functions: {self.metrics.documented_functions}")
        report.append(f"Documented classes: {self.metrics.documented_classes}")
        report.append(f"Documentation coverage: {self.metrics.documentation_coverage:.1f}%")
        
        if self.metrics.documentation_coverage < 80:
            report.append("⚠️  Documentation coverage below recommended 80%")
        else:
            report.append("✅ Good documentation coverage")
        report.append("")
        
        # Complexity metrics
        report.append("CODE COMPLEXITY")
        report.append("-" * 15)
        report.append(f"Average function length: {self.metrics.average_function_length:.1f} lines")
        report.append(f"Maximum function length: {self.metrics.max_function_length} lines")
        report.append(f"Complex functions (>50 lines): {self.metrics.complex_functions}")
        
        if self.metrics.complex_functions > 0:
            report.append("⚠️  Complex functions detected - consider refactoring")
        else:
            report.append("✅ No overly complex functions detected")
        report.append("")
        
        # Error handling metrics
        report.append("ERROR HANDLING")
        report.append("-" * 14)
        report.append(f"Functions with error handling: {self.metrics.functions_with_error_handling}")
        report.append(f"Error handling coverage: {self.metrics.error_handling_coverage:.1f}%")
        
        if self.metrics.error_handling_coverage < 60:
            report.append("⚠️  Error handling coverage below recommended 60%")
        else:
            report.append("✅ Good error handling coverage")
        report.append("")
        
        # Code style metrics
        report.append("CODE STYLE")
        report.append("-" * 10)
        report.append(f"Style violations: {self.metrics.style_violations}")
        report.append(f"Naming violations: {self.metrics.naming_violations}")
        
        if self.metrics.style_violations + self.metrics.naming_violations == 0:
            report.append("✅ No style violations detected")
        else:
            report.append("⚠️  Style violations detected - review coding standards")
        report.append("")
        
        # Maintainability metrics
        report.append("MAINTAINABILITY")
        report.append("-" * 13)
        report.append(f"Maintainability score: {self.metrics.maintainability_score:.1f}/100")
        report.append(f"Technical debt indicators: {self.metrics.technical_debt_indicators}")
        
        if self.metrics.maintainability_score >= 80:
            report.append("✅ Excellent maintainability")
        elif self.metrics.maintainability_score >= 60:
            report.append("⚠️  Good maintainability with room for improvement")
        else:
            report.append("❌ Poor maintainability - significant improvements needed")
        report.append("")
        
        # Integration quality metrics
        report.append("INTEGRATION QUALITY")
        report.append("-" * 18)
        report.append(f"Integration issues: {self.metrics.integration_issues}")
        report.append(f"Compatibility issues: {self.metrics.compatibility_issues}")
        
        if self.metrics.integration_issues + self.metrics.compatibility_issues == 0:
            report.append("✅ No integration issues detected")
        else:
            report.append("⚠️  Integration issues detected - review integration quality")
        report.append("")
        
        # Issues summary
        if self.issues:
            report.append("ISSUES DETECTED")
            report.append("-" * 15)
            for i, issue in enumerate(self.issues[:20], 1):  # Show first 20 issues
                report.append(f"{i:2d}. {issue}")
            
            if len(self.issues) > 20:
                report.append(f"... and {len(self.issues) - 20} more issues")
            report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 15)
        
        if self.metrics.documentation_coverage < 80:
            report.append("• Improve documentation coverage by adding docstrings")
        
        if self.metrics.complex_functions > 0:
            report.append("• Refactor complex functions into smaller, more manageable pieces")
        
        if self.metrics.error_handling_coverage < 60:
            report.append("• Add error handling to functions that interact with external resources")
        
        if self.metrics.style_violations > 0:
            report.append("• Fix code style violations to improve readability")
        
        if self.metrics.technical_debt_indicators > 10:
            report.append("• Address TODO/FIXME comments to reduce technical debt")
        
        if self.metrics.integration_issues > 0:
            report.append("• Review integration-specific code for quality and compatibility")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_report(self, filename: str = "code_quality_report.txt"):
        """
        Save code quality report to file.
        
        Args:
            filename: Output filename
        """
        report = self.generate_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Code quality report saved to {filename}")
    
    def get_recommendations(self) -> List[str]:
        """
        Get specific recommendations for code quality improvement.
        
        Returns:
            List of actionable recommendations
        """
        recommendations = []
        
        # Documentation recommendations
        if self.metrics.documentation_coverage < 80:
            recommendations.append(
                "Add comprehensive docstrings to all public functions and classes. "
                "Include parameter descriptions, return values, and usage examples."
            )
        
        # Complexity recommendations
        if self.metrics.complex_functions > 0:
            recommendations.append(
                "Break down complex functions (>50 lines) into smaller, single-purpose functions. "
                "Use helper methods and extract common functionality."
            )
        
        # Error handling recommendations
        if self.metrics.error_handling_coverage < 60:
            recommendations.append(
                "Add try-except blocks to functions that perform file I/O, network operations, "
                "or device communication. Provide meaningful error messages and recovery options."
            )
        
        # Style recommendations
        if self.metrics.style_violations > 0:
            recommendations.append(
                "Follow PEP 8 style guidelines. Keep lines under 100 characters, "
                "use proper spacing, and follow naming conventions."
            )
        
        # Maintainability recommendations
        if self.metrics.technical_debt_indicators > 10:
            recommendations.append(
                "Address TODO and FIXME comments. Either implement the required functionality "
                "or remove outdated comments."
            )
        
        # Integration recommendations
        if self.metrics.integration_issues > 0:
            recommendations.append(
                "Ensure all integration points have proper error handling and backward compatibility. "
                "Add comprehensive tests for integrated functionality."
            )
        
        return recommendations


def main():
    """Main function to run code quality validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate MRUpdater code quality")
    parser.add_argument(
        "--path", 
        default=".", 
        help="Path to analyze (default: current directory)"
    )
    parser.add_argument(
        "--output", 
        default="code_quality_report.txt",
        help="Output report filename"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run validation
    validator = CodeQualityValidator(args.path)
    metrics = validator.validate_all()
    
    # Generate and save report
    validator.save_report(args.output)
    
    # Print summary
    print(f"\nCode Quality Validation Summary:")
    print(f"Files analyzed: {metrics.total_files}")
    print(f"Documentation coverage: {metrics.documentation_coverage:.1f}%")
    print(f"Error handling coverage: {metrics.error_handling_coverage:.1f}%")
    print(f"Maintainability score: {metrics.maintainability_score:.1f}/100")
    print(f"Issues found: {len(validator.issues)}")
    print(f"\nDetailed report saved to: {args.output}")
    
    # Exit with appropriate code
    if metrics.maintainability_score < 60 or len(validator.issues) > 50:
        print("\n❌ Code quality validation failed - significant improvements needed")
        sys.exit(1)
    elif metrics.maintainability_score < 80 or len(validator.issues) > 20:
        print("\n⚠️  Code quality validation passed with warnings")
        sys.exit(0)
    else:
        print("\n✅ Code quality validation passed")
        sys.exit(0)


if __name__ == "__main__":
    main()