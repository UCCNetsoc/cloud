package v1

import (
	"net/http"
	"encoding/json"
	
	chi "github.com/go-chi/chi"
	consul "github.com/hashicorp/consul/api"
	websites "websites/pkg"
)

type WebsitesEndpoint struct {
	provider websites.Provider
}

// InjectWebsites a
func InjectWebsites(provider websites.Provider) func(r chi.Router) {
	return func(r chi.Router) {
		e := &WebsitesEndpoint{
			provider: provider
		}
	
		r.Post("/", e.Create)
	}
}


func (e *WebsitesEndpoint) Create(w http.ResponseWriter, h *http.Request) {
	var userOpts websites.WebsiteUserOpts
	err := json.NewDecoder(r.Body).Decode(&UserOpts)

	if err != nil {
		http.Error(w, json.Marshal(&Info{
			detail: &Detail{
				msg: "Invalid body supplied. " + err.Error()
			}
		}), http.StatusUnprocessableEntity)
		return
	}

	err := e.provider.Create(&websites.Website{
		WebsiteUserOpts: userOpts,
		User: "ocanty",
	})

	if err != nil {
		http.Error(w, json.Marshal(&Info{
			detail: &Detail{
				msg: "Could not create website. " + err.Error()
			}
		}), http.StatusUnprocessableEntity)
		return
	}
}