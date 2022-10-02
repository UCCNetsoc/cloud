import { RingProgress, Text } from "@mantine/core"

const ResourceRing = (props: { current: number, max: number, label?: string, size?: number, longlabel?: string, outsidelabel?: string, decimals?: number }) => {

  const usage = parseFloat((props.current / props.max).toFixed(props.decimals || 2));

  return (
    <span style={{ display: "flex", alignItems: "center" }}>
      <RingProgress
        sections={[
          {
            value: usage,
            color: usage > 80 ? "red" : usage > 60 ? "yellow" : "green",
          }
        ]}
        thickness={4}
        label={
          <Text sx={{ display: "inline-block", margin: "auto", lineHeight: 1.2, textAlign: "center", width: "100%" }}>
            {props.label !== undefined ? props.label : props.longlabel ? `${usage}% of ${parseFloat(props.longlabel).toFixed(props.decimals || 2)}G` : `${usage}%`}
          </Text>
        }

        size={props.size ? props.size : 100}

      />
      {props.outsidelabel && <Text sx={{ display: "inline-block", margin: "auto", lineHeight: 1.2, textAlign: "center", width: "100%" }}>
        {usage.toFixed(0)}% of {props.outsidelabel}G
      </Text>}
    </span>
  )
}

export default ResourceRing
