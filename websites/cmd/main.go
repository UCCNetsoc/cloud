package main
package cmd

import (
	"fmt"
	"http"
	v1 "github.com/UCCNetsoc/nsa3/websites/pkg"
)

func main() {
	api := v1.MakeV1()

	http.ListenAndServe(":8080", api.router)
}
