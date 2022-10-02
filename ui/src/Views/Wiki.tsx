import { useEffect } from "react"
import { useNavigate } from "react-router"

const Wiki = () => {
  window.open("https://wiki.netsoc.co/en/services/tutorial")
  const navigate = useNavigate()
  
  useEffect(() => {navigate("/")}, [])

  return <>Redirecting...</>
}

export default Wiki
