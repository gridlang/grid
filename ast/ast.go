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
	LogicalOr *LogicalOrExpression `parser:"@@"`
}

type LogicalOrExpression struct {
	Left  *LogicalAndExpression   `parser:"@@"`
	Right []*LogicalAndExpression `parser:"( @LogicalOrOp @@ )*"`
}

type LogicalAndExpression struct {
	Left  *EqualityExpression   `parser:"@@"`
	Right []*EqualityExpression `parser:"( @LogicalAndOp @@ )*"`
}

type EqualityExpression struct {
	Left  *RelationalExpression   `parser:"@@"`
	Right []*RelationalExpression `parser:"( @EqualityOp @@ )*"`
}

type RelationalExpression struct {
	Left  *AdditiveExpression   `parser:"@@"`
	Right []*AdditiveExpression `parser:"( @RelationalOp @@ )*"`
}

type AdditiveExpression struct {
	Left  *MultiplicativeExpression   `parser:"@@"`
	Right []*MultiplicativeExpression `parser:"( @AdditiveOp @@ )*"`
}

type MultiplicativeExpression struct {
	Left  *UnaryExpression   `parser:"@@"`
	Right []*UnaryExpression `parser:"( @MultiplicativeOp @@ )*"`
}

type UnaryExpression struct {
	Operator *string            `parser:"( @UnaryOp )?"`
	Primary  *PrimaryExpression `parser:"@@"`
}

type PrimaryExpression struct {
	Literal      *Literal      `parser:"@Literal"`
	Ident        *string       `parser:"| @Ident"`
	SubExpr      *Expr         `parser:"| '(' @@ ')'"`
	FuncCall     *FunctionCall `parser:"| @@"`
	ArrayLiteral *ArrayLiteral `parser:"| @@"`
	MapLiteral   *MapLiteral   `parser:"| @@"`
	Tuple        *Tuple        `parser:"| @@"`
	StructTuple  *StructTuple  `parser:"| @@"`
	Block        *BlockLiteral `parser:"| @@"`
}

type Literal struct {
	Bool   *string `parser:"@Bool"`
	Int    *string `parser:"| @Int"`
	Num    *string `parser:"| @Num"`
	Char   *string `parser:"| @Char"`
	String *string `parser:"| @String"`
}

type FunctionCall struct {
	Name      string  `parser:"@Ident '('"`
	Arguments []*Expr `parser:"( @@ ( ',' @@ )* )? ')'"`
}

type ArrayLiteral struct {
	Elements []*Expr `parser:"'[' @@ ( ',' @@ )* ']'"`
}

type MapEntry struct {
	Key   *Expr `parser:"@@ ':'"`
	Value *Expr `parser:"@@"`
}

type MapLiteral struct {
	Entries []*MapEntry `parser:"'{' @@ ( ',' @@ )* '}'"`
}

type Tuple struct {
	Elements []*Expr `parser:"'(' @@ ( ',' @@ )* ')'"`
}

type StructTuple struct {
	Fields []*StructField `parser:"'(' @@ ( ',' @@ )* ')'"`
}

type StructField struct {
	Name string `parser:"@Ident ':'"`
	Type *Expr  `parser:"@@"`
}

type BlockLiteral struct {
	Statements []*Statement `parser:"'{' @@* '}'"`
}

