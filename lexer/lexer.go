package lexer

import (
	"github.com/alecthomas/participle/v2/lexer"
)

var GridLexer = lexer.MustSimple([]lexer.SimpleRule{
	{Name: "Ident", Pattern: `[\w_][\w\d_]*`},
	{Name: "Bool", Pattern: `true|false`},
	{Name: "Int", Pattern: `\d+`},
	{Name: "Num", Pattern: `\d+(\.\d+)?([eE][+-]?\d+)?`},
	{Name: "Char", Pattern: `'.'`},
	{Name: "String", Pattern: `"(\\.|[^"])*"`},
	{Name: "LogicalOrOp", Pattern: `\|\|`},
	{Name: "LogicalAndOp", Pattern: `&&`},
	{Name: "EqualityOp", Pattern: `==|!=`},
	{Name: "RelationalOp", Pattern: `<=|>=|<|>`},
	{Name: "AdditiveOp", Pattern: `[-+]`},
	{Name: "MultiplicativeOp", Pattern: `[*/%^]`},
	{Name: "UnaryOp", Pattern: `[!+-]`}, // Including unary + and -
	{Name: "Comment", Pattern: `//.*`},
	{Name: "Whitespace", Pattern: `\s+`},
})
