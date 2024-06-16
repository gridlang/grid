package ast

type Program struct {
	Statements []*Statement `parser:"@@*"`
}

type Statement struct {
	Assignment *Assignment `parser:"@@"`
}

type Assignment struct {
	Name  string `parser:"@Ident"`
	Value *Expr  `parser:"'=' @@"`
}

type Expr struct {
	Term  *Term  `parser:"@@"`
	Op    string `parser:"[ @Operator"`
	Right *Expr  `parser:"@@ ]"`
}

type Term struct {
	Ident  *string `parser:"@Ident"`
	Number *int    `parser:"| @Number"`
}
