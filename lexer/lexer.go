package lexer

import (
	"github.com/alecthomas/participle/v2/lexer"
)

var GridLexer = lexer.MustSimple([]lexer.SimpleRule{
	{Name: "Ident", Pattern: `[a-zA-Z_][a-zA-Z0-9_]*`},
	{Name: "Number", Pattern: `\d+`},
	{Name: "Operator", Pattern: `[-+*/=]`},
	{Name: "Punct", Pattern: `[{}(),;]`},
	{Name: "Comment", Pattern: `//.*`},
	{Name: "Whitespace", Pattern: `\s+`},
})
