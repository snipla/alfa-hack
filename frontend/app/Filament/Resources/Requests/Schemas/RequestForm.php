<?php

namespace App\Filament\Resources\Requests\Schemas;

use App\Models\Request;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Textarea;
use Filament\Schemas\Schema;

class RequestForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextInput::make('user_id')
                    ->required()
                    ->numeric(),
                Select::make('status')
                    ->options([
                        Request::REQUEST_CREATED => 'Отправлено',
                        Request::REQUEST_IN_PROCESS => 'В обработке',
                        Request::REQUEST_ACCEPTED => 'Принято',
                        Request::REQUEST_REJECTED => 'Отклонено',

                    ])
                    ->required()
                    ->default(Request::REQUEST_IN_PROCESS),
//                TextInput::make('status')
//                    ->required()
//                    ->default('created'),
                Textarea::make('credit_info')
                    ->default(null)
                    ->columnSpanFull(),
            ]);
    }
}
