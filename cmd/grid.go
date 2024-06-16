package main

import (
	"fmt"
	"os"

	// "grid/compiler"
	"grid/ast"
	"grid/parser"

	"github.com/charmbracelet/log"
	"github.com/spf13/pflag"
)

var logLevel string

func init() {
	// Define the log level flag with both short and long names
	pflag.StringVarP(
		&logLevel,
		"loglevel",
		"l",
		"info",
		"set the log level (debug, info, warn, error, fatal)",
	)

	// Set the custom usage function
	pflag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s [options] <filename>\n", os.Args[0])
		fmt.Fprintf(os.Stderr, "Options:\n")
		pflag.PrintDefaults()
	}

	// Parse the command-line flags
	pflag.Parse()

	// Set the log level based on the flag
	switch logLevel {
	case "debug":
		log.SetLevel(log.DebugLevel)
	case "info":
		log.SetLevel(log.InfoLevel)
	case "warn":
		log.SetLevel(log.WarnLevel)
	case "error":
		log.SetLevel(log.ErrorLevel)
	case "fatal":
		log.SetLevel(log.FatalLevel)
	default:
		log.SetLevel(log.InfoLevel)
	}

	// Check if the program was called with no arguments or with --help
	if pflag.NArg() == 0 {
		pflag.Usage()
		os.Exit(1)
	}
}

func printAST(p *ast.Program) {
	for stmt := range p.Statements {
		fmt.Printf("stmt: %v\n", stmt)
	}
}

func main() {
	filename := pflag.Arg(0)

	log.Debugf("Opening file: %s", filename)
	file, err := os.Open(filename)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	log.Debug("Parsing code")
	program := parser.Parse(filename, file)
	printAST(program)
	// log.Debug("Compiling code")
	// compiler.GenerateNASM(program)
}
