package api

import (
	"net/http"
	v1 "github.com/UCCNetsoc/nsa3/routes/app/api/v1"
	
	"github.com/go-chi/chi"

)

type API struct {
	routes chi.Router
}

func (api *API) Init() {
	api.routes.Route("/v1", func(r chi.Router) {
		v1.AddRoutes(r)
	})
}
