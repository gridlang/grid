package compiler

import (
	"fmt"

	"grid/ast"
)

func GenerateNASM(program *ast.Program) {
	fmt.Println("section .data")
	fmt.Println("section .text")
	fmt.Println("global _start")
	fmt.Println("_start:")

	for _, stmt := range program.Statements {
		if stmt.Assignment != nil {
			generateAssignment(stmt.Assignment)
		}
	}

	fmt.Println("mov eax, 1")
	fmt.Println("int 0x80")
}

func generateAssignment(assign *ast.Assignment) {
	fmt.Printf("mov [%s], ", assign.Name)
	generateExpr(assign.Value)
	fmt.Println()
}

func generateExpr(expr *ast.Expr) {
	if expr.Op == "" {
		generateTerm(expr.Term)
	} else {
		generateExpr(expr.Right)
		fmt.Printf(" %s ", expr.Op)
		generateTerm(expr.Term)
	}
}

func generateTerm(term *ast.Term) {
	if term.Ident != nil {
		fmt.Printf("[%s]", *term.Ident)
	} else if term.Number != nil {
		fmt.Printf("%d", *term.Number)
	}
}
