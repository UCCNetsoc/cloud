package v1

import (
	"net/http"
	"github.com/go-chi/chi"

	models "github.com/UCCNetsoc/nsa3/routes/app/api/v1/models"
)

type VirtualHost struct {
	Host string `json:"name"`
	Path string `json:"path"`
}

#api.netsoc.co/v1/routes/virtual-host

func create(w http.ResponseWriter, r *http.Request) {
	var vhost VirtualHost
}

func AddRoutes(r chi.Router) {
	r.Route("/virtual-hosts", func(r chi.Router) {
		r.Post("/", create)
	})
}


