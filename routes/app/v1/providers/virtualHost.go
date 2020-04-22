package virtualHost

import (
	"fmt"
	"crypto/sha256"
	"encoding/hex"

	models		"github.com/UCCNetsoc/nsa3/routes/api/v1/models"
	traefikConfig	"github.com/UCCNetsoc/nsa3/routes/api/v1/providers/traefikConfig"
)

interface Provider {
	CreateVirtualHost(v *models.VirtualHost) error
}

type struct Traefik {
	config traefikConfig.Config
}

func NewTraefik(conf traefikConfig.Config) {
	return &Traefik{
		config: conf
	}
}

func (p *Traefik) CreateVirtualHost(v *models.VirtualHost) error {
	checksum := sha256.Sum256([]byte(v.Host))
	hash := hex.EncodeAsString(checksum)

	var router			string	= "nsa3-routes-" + hash
	var service			string	= "nsa3-service-" + hash
	var middlewareHeaders		string	= "nsa3-middleware-headers-" + hash
	var middlewarePrefix		string	= "nsa3-middleware-prefix-" + hash
	var routerBaseKey		string	= "http.routers." + router
	var serviceBaseKey		string	= "http.services." + service
	var middlewareHeadersBaseKey	string	= "http.middlewares." + middlewareHeaders
	var middlewarePrefixBaseKey	string	= "http.middlewares." + middlewarePrefix

	kv := make(map[string]string)
	kv[routerBaseKey + ".rule"]		= "Host(`" + v.Host + "`)"
	kv[routerBaseKey + ".service"]		= service
	kv[routerBaseKey + ".middlewares"]	= middlewareHeaders + "," + middlewarePrefix

	for header, value := range v.AdditionalRequestHeaders {
		kv[middlewareHeadersBaseKey + ".headers.customRequestHeaders." + header] = value
	}

	kv[middlewarePrefixBaseKey + ".addPrefix.prefix"] = v.PrefixPath
	kv[serviceBaseKey + ".loadBalancer.servers"] = v.DestinationServer

	err := p.config.SetKVs(kv)
	if err != nil {
		return err
	}

	return nil
}


