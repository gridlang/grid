package parser

import (
	"io"

	"grid/ast"
	"grid/lexer"

	"github.com/alecthomas/participle/v2"
	"github.com/charmbracelet/log"
)

func Parse(filename string, file io.Reader) *ast.Program {
	log.Debug("Constructing parser")
	var parser = participle.MustBuild[ast.Program](
		participle.Lexer(lexer.GridLexer),
		participle.Elide("Whitespace", "Comment"),
	)

	log.Debugf("Parsing %s", filename)
	program, err := parser.Parse(filename, file)
	if err != nil {
		log.Errorf("Error parsing file: %s\n", err)
	}

	return program
}
