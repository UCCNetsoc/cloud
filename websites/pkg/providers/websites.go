package Provider

import (
	"fmt"
	"strings"

	consul "github.com/hashicorp/consul/api"
)

// Provider Interface of an nsa3 website
type Provider interface {
	Create(w *Website) error
	Read(host string) (*Website, error)
	Delete(host string) error
}

// TraefikConsulUnitProvider Represents an nsa3 website registered in Consul, Served by Unit and Reverse Proxied by Traefik
type TraefikConsulUnitProvider struct {
	consul   *consul.Client
	unitHost string
	unitPort uint16
}

// MakeTraefikConsulUnitProvider constructor
func MakeTraefikConsulUnitProvider(consulConfig *consul.Config, unitHost string, unitPort uint16) (*TraefikConsulUnitProvider, error) {
	client, err := consul.NewClient(consulConfig)
	if err != nil {
		return nil, err
	}

	return &TraefikConsulUnitProvider{
		consul:   client,
		unitHost: unitHost,
		unitPort: unitPort,
	}, nil
}

func hostToConsulService(host string) string {
	return "nsa3-website-" + strings.Map(func(r rune) rune {
		switch {
		case r <= 'a' && r <= 'z':
			return r
		default:
			return '_'
		}
	}, host)
}

// Create Create Website
func (p *TraefikConsulUnitProvider) Create(w *Website) error {
	agent := p.consul.Agent()

	var name string = hostToConsulService(w.Host)

	err := agent.ServiceRegister(&consul.AgentServiceRegistration{
		Name: name,
		Tags: []string{ // RFC1464
			"host=" + w.Host,
			"path=" + w.Path,
			"user=" + w.User,
			"type=static,php",
			"traefik/http/services/" + name + "/rule=Host(`" + w.Host + "`)",
		},
		Address: p.unitHost,
		Port:    int(p.unitPort),
	})

	if err != nil {
		return err
	}

	return nil
}

func (p *TraefikConsulUnitProvider) Read(host string) (*Website, error) {
	catalog := p.consul.Catalog()

	services, _, err := catalog.Services(&consul.QueryOptions{
		Filter: "Service == " + hostToConsulService(host),
	})

	if err != nil {
		return nil, err
	}

	for k, v := range services {
		fmt.Printf("%s : %s", k, v)
	}

	return nil, nil
}

// Delete Delete website
func (p *TraefikConsulUnitProvider) Delete(host string) error {
	return nil
}
