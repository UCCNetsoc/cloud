import { useEffect } from "react"
import { useNavigate } from "react-router"

const Wiki = () => {
  window.open("https://wiki.netsoc.co")
  const navigate = useNavigate()
  
  useEffect(() => {navigate("/")}, [])

  return <>Redirecting...</>
}

export default Wiki
