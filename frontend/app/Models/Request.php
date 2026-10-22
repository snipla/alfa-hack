<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Request extends Model
{
    public const  REQUEST_CREATED = 'created';
    public const REQUEST_IN_PROCESS = 'in_process';
    public const REQUEST_ACCEPTED = 'accepted';
    public const REQUEST_REJECTED = 'rejected';

    public $fillable = [
        'user_id',
        'status',
        'credit_info',
        'admin_comment'
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
