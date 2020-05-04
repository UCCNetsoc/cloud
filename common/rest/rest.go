package rest

import (
	"encoding/json"
	"net/http"
)

type Detail struct {
	Msg string   `json:"msg"`
	Loc []string `json:"loc",omitempty`
}

type Info struct {
	Detail *Detail `json:"detail"`
}

type Error struct {
	Detail *Detail `json:"detail"`
}

func WriteError(w http.ResponseWriter, code int, detail *Detail) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(&Error{
		Detail: detail,
	})
}
