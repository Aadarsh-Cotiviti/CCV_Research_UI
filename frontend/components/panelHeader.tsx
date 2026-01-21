import { FC } from "react"

interface Props {
    title: string,
    subTitle: string
    icon?: React.ReactNode
}

export const PanelHeader: FC<Props> = ({ title, subTitle, icon }) => {
    return <div className="p-4 border-0 border-b">
        {icon}
        <div className="">
            <h2 className="text-2xl font-semibold">
                {title}
            </h2>
            <p className="text-sm text-muted-foreground">{subTitle}</p>
        </div>
    </div>
}