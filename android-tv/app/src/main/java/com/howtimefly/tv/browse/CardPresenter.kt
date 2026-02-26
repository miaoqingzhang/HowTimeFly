package com.howtimefly.tv.browse

import android.graphics.drawable.Drawable
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.leanback.widget.ImageCardView
import androidx.leanback.widget.Presenter
import com.bumptech.glide.Glide
import com.howtimefly.tv.R

/**
 * 媒体卡片展示器
 */
class CardPresenter : Presenter() {

    override fun onCreateViewHolder(parent: ViewGroup): ViewHolder {
        val cardView = ImageCardView(parent.context).apply {
            isFocusable = true
            isFocusableInTouchMode = true
            setMainImageDimensions(
                CARD_WIDTH,
                CARD_HEIGHT
            )
        }
        return ViewHolder(cardView)
    }

    override fun onBindViewHolder(viewHolder: ViewHolder, item: Any) {
        val card = item as MediaCard
        val cardView = viewHolder.view as ImageCardView

        cardView.titleText = card.title
        cardView.contentText = card.subtitle

        // 视频标识
        if (card.isVideo) {
            val badge = ContextCompat.getDrawable(
                cardView.context,
                R.drawable.ic_play_circle
            )
            cardView.setBadgeImage(badge)
        }

        // 加载缩略图
        if (!card.imageUrl.isNullOrEmpty()) {
            Glide.with(cardView.context)
                .load(card.imageUrl)
                .centerCrop()
                .placeholder(R.drawable.ic_placeholder)
                .error(R.drawable.ic_error)
                .into(cardView.mainImageView)
        } else {
            cardView.mainImage = ContextCompat.getDrawable(
                cardView.context,
                if (card.isVideo) R.drawable.ic_video_placeholder else R.drawable.ic_photo_placeholder
            )
        }
    }

    override fun onUnbindViewHolder(viewHolder: ViewHolder) {
        val cardView = viewHolder.view as ImageCardView
        // 清除图片，避免内存泄漏
        Glide.with(cardView.context).clear(cardView.mainImageView)
    }

    companion object {
        private const val CARD_WIDTH = 313
        private const val CARD_HEIGHT = 176
    }
}
