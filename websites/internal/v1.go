package v1

import (
	websites "github.com/UCCNetsoc/nsa3/websites/pkg"

	chi "github.com/go-chi/chi"
	middleware "github.com/go-chi/chi/middleware"
	consul "github.com/hashicorp/consul/api"
)

// API Base API type
type API interface {
	Serve()
}

// V1 V1 of the websites API
type V1 struct {
	router chi.Router
}

// MakeV1 makes an instance of API version 1
func MakeV1() (*V1, error) {
	consulConfig := consul.DefaultConfig()
	consulConfig.Address = "consul.netsoc.local:8500"

	websitesProvider := websites.MakeTraefikConsulUnitProvider(consulConfig, "nginx_unit:6300")

	r := chi.NewRouter()
	r.Use(middleware.Logger)

	r.Route("/v1", func(r chi.Router) {
		r.Route("/websites", InjectWebsites(websitesProvider))
	})

	return &V1{
		router: r,
	}, nil
}
